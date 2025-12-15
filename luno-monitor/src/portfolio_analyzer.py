"""
Portfolio Analyzer Module
Analyzes portfolio holdings and calculates metrics
"""
from typing import Dict, List
from datetime import datetime
import config
from src.luno_client import LunoClient
from src.price_monitor import PriceMonitor
from src.currency_converter import CurrencyConverter

class PortfolioAnalyzer:
    """Analyze cryptocurrency portfolio"""
    
    def __init__(self):
        """Initialize portfolio analyzer"""
        self.luno_client = LunoClient()
        self.price_monitor = PriceMonitor()
        self.currency = CurrencyConverter()
        
        # Update exchange rate on init
        self.currency.update_exchange_rate()
    
    def get_portfolio_snapshot(self) -> Dict:
        """
        Get complete portfolio snapshot with all metrics
        
        Returns:
            Dictionary with portfolio data
        """
        # Get balances from Luno
        balances = self.luno_client.get_balances()
        
        # Get current prices
        current_prices = self.price_monitor.get_all_prices()
        
        holdings = []
        total_value_myr = 0
        total_cost_basis = 0
        
        for coin, balance_info in balances.items():
            if balance_info['balance'] == 0:
                continue
            
            # Get current price
            current_price = current_prices.get(coin, 0)
            
            # Calculate average buy price (simplified - would need actual transaction history)
            avg_buy_price, total_amount, txn_count = self.luno_client.calculate_average_buy_price(coin)
            
            # Calculate target prices
            target_prices = self.luno_client.calculate_target_prices(avg_buy_price, coin)
            
            # Calculate current value
            current_value = balance_info['balance'] * current_price
            cost_basis = balance_info['balance'] * avg_buy_price
            
            # Calculate profit/loss
            pl_metrics = self.price_monitor.calculate_profit_loss(coin, avg_buy_price, current_price)
            
            # Get price trend
            trend = self.price_monitor.get_price_trend(coin, hours=24)
            
            holdings.append({
                'coin': coin,
                'balance': balance_info['balance'],
                'avg_buy_price': avg_buy_price,
                'current_price': current_price,
                'current_value': current_value,
                'cost_basis': cost_basis,
                'profit_loss_myr': current_value - cost_basis,
                'profit_loss_pct': pl_metrics['profit_loss_percent'],
                'status': pl_metrics['status'],
                'target_prices': target_prices,
                'trend': trend,
                'targets_reached': self._check_targets_reached(current_price, target_prices)
            })
            
            total_value_myr += current_value
            total_cost_basis += cost_basis
        
        # Calculate overall metrics
        total_profit_loss = total_value_myr - total_cost_basis
        total_profit_pct = (total_profit_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        # Sort holdings by value (descending)
        holdings.sort(key=lambda x: x['current_value'], reverse=True)
        
        return {
            'timestamp': datetime.now(),
            'total_value': total_value_myr,
            'total_cost_basis': total_cost_basis,
            'total_profit_loss': total_profit_loss,
            'total_profit_pct': total_profit_pct,
            'holdings': holdings,
            'num_coins': len(holdings),
            'best_performer': self._get_best_performer(holdings),
            'worst_performer': self._get_worst_performer(holdings)
        }
    
    def _check_targets_reached(self, current_price: float, target_prices: Dict[float, float]) -> List[float]:
        """Check which profit targets have been reached"""
        reached = []
        for profit_pct, target_price in target_prices.items():
            if current_price >= target_price:
                reached.append(profit_pct)
        return reached
    
    def _get_best_performer(self, holdings: List[Dict]) -> Dict:
        """Get best performing coin by profit percentage"""
        if not holdings:
            return {}
        
        best = max(holdings, key=lambda x: x['profit_loss_pct'])
        return {
            'coin': best['coin'],
            'profit_pct': best['profit_loss_pct'],
            'value': best['current_value']
        }
    
    def _get_worst_performer(self, holdings: List[Dict]) -> Dict:
        """Get worst performing coin by profit percentage"""
        if not holdings:
            return {}
        
        worst = min(holdings, key=lambda x: x['profit_loss_pct'])
        return {
            'coin': worst['coin'],
            'profit_pct': worst['profit_loss_pct'],
            'value': worst['current_value']
        }
    
    def generate_summary_report(self) -> str:
        """
        Generate text summary report of portfolio
        
        Returns:
            Formatted text report
        """
        snapshot = self.get_portfolio_snapshot()
        
        report = []
        report.append("=" * 70)
        report.append("LUNO PORTFOLIO SUMMARY")
        report.append("=" * 70)
        report.append(f"Timestamp: {snapshot['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append(f"Total Portfolio Value: {self.currency.format_myr_primary(snapshot['total_value'])}")
        report.append(f"Total Cost Basis:      {self.currency.format_myr_primary(snapshot['total_cost_basis'])}")
        report.append(f"Total Profit/Loss:     {self.currency.format_myr_primary(snapshot['total_profit_loss'])} ({snapshot['total_profit_pct']:+.2f}%)")
        report.append("")
        
        if snapshot['best_performer']:
            bp = snapshot['best_performer']
            report.append(f"🏆 Best Performer:  {bp['coin']} ({bp['profit_pct']:+.2f}%)")
        
        if snapshot['worst_performer']:
            wp = snapshot['worst_performer']
            report.append(f"📉 Worst Performer: {wp['coin']} ({wp['profit_pct']:+.2f}%)")
        
        report.append("")
        report.append("=" * 70)
        report.append("HOLDINGS")
        report.append("=" * 70)
        
        for holding in snapshot['holdings']:
            report.append(f"\n{holding['coin']}")
            report.append(f"  Balance:       {holding['balance']:.8f}")
            report.append(f"  Avg Buy Price: {self.currency.format_myr_primary(holding['avg_buy_price'])}")
            report.append(f"  Current Price: {self.currency.format_myr_primary(holding['current_price'])}")
            report.append(f"  Current Value: {self.currency.format_myr_primary(holding['current_value'])}")
            report.append(f"  Profit/Loss:   {self.currency.format_myr_primary(holding['profit_loss_myr'])} ({holding['profit_loss_pct']:+.2f}%)")
            
            if holding['targets_reached']:
                report.append(f"  🎯 Targets Reached: {', '.join([f'{t}%' for t in holding['targets_reached']])}")
            
            report.append(f"  Next Targets:")
            for pct, price in sorted(holding['target_prices'].items()):
                status = "✓" if pct in holding['targets_reached'] else " "
                report.append(f"    [{status}] {pct}%: {self.currency.format_myr_primary(price)}")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)


if __name__ == "__main__":
    # Test portfolio analyzer
    print("Testing Portfolio Analyzer...")
    
    analyzer = PortfolioAnalyzer()
    report = analyzer.generate_summary_report()
    
    print(report)
