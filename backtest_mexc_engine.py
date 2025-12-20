#!/usr/bin/env python3
"""
Enhanced Backtest Engine for MEXC Migration
Supports ANY strategy with MEXC-specific fee structure

CRITICAL DATA SEPARATION:
- Backtest results stored in: backtest_results/
- Database: trades_mexc_backtest.db (SEPARATE from Binance)
- All trades tagged with: exchange='MEXC', mode='backtest'
"""
import pandas as pd
import os
from datetime import datetime
from decimal import Decimal
import json
import sys

class MEXCBacktestEngine:
    """
    Universal backtest engine for MEXC exchange
   
    Simulates trading with MEXC-specific characteristics:
    - Maker fee: 0.0% (free)
    - Taker fee: 0.05% (0.025% with 500+ MX tokens)
    - Slippage: 0.1-0.3% (estimated from depth)
    """
    
    def __init__(self, strategy_name, initial_capital=1000, use_mx_discount=True):
        self.strategy_name = strategy_name
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.closed_trades = []
        
        # MEXC Fee Structure
        self.maker_fee = 0.0000   # 0% maker
        self.taker_fee = 0.00025 if use_mx_discount else 0.0005  # 0.025% or 0.05%
        self.slippage = 0.002  # 0.2% average slippage
        
        # Exchange metadata for ALL trades
        self.exchange = 'MEXC'
        self.mode = 'backtest'
        
        print(f"{'='*80}")
        print(f"MEXC Backtest Engine Initialized")
        print(f"{'='*80}")
        print(f"Strategy: {strategy_name}")
        print(f"Initial Capital: ${initial_capital:,.2f}")
        print(f"Maker Fee: {self.maker_fee*100:.3f}%")
        print(f"Taker Fee: {self.taker_fee*100:.3f}%")
        print(f"Estimated Slippage: {self.slippage*100:.2f}%")
        print(f"Exchange: {self.exchange}")
        print(f"Mode: {self.mode}")
        print(f"{'='*80}\n")
    
    def open_position(self, symbol, entry_price, amount, timestamp, reason=""):
        """Open a new position"""
        # Simulate taker order (market order)
        actual_price = entry_price * (1 + self.slippage)  # Slippage
        cost = actual_price * amount
        fee = cost * self.taker_fee
        total_cost = cost + fee
        
        if total_cost > self.capital:
            print(f"  ⚠️ Insufficient capital: ${self.capital:.2f} < ${total_cost:.2f}")
            return False
        
        position = {
            'symbol': symbol,
            'entry_price': actual_price,
            'amount': amount,
            'cost': cost,
            'entry_fee': fee,
            'entry_time': timestamp,
            'reason': reason,
            'exchange': self.exchange,  # Tag with exchange
            'mode': self.mode,          # Tag with mode
        }
        
        self.positions.append(position)
        self.capital -= total_cost
        
        print(f"  📈 BUY: {amount:.4f} {symbol} @ ${actual_price:.4f} (Fee: ${fee:.2f})")
        
        return True
    
    def close_position(self, symbol, exit_price, timestamp, reason=""):
        """Close an existing position"""
        # Find matching position (FIFO)
        position = None
        for i, pos in enumerate(self.positions):
            if pos['symbol'] == symbol:
                position = self.positions.pop(i)
                break
        
        if not position:
            print(f"  ⚠️  No open position for {symbol}")
            return False
        
        # Simulate taker order
        actual_price = exit_price * (1 - self.slippage)  # Slippage
        proceeds = actual_price * position['amount']
        exit_fee = proceeds * self.taker_fee
        net_proceeds = proceeds - exit_fee
        
        # Calculate P&L
        pnl = net_proceeds - position['cost']
        pnl_pct = (pnl / position['cost']) * 100
        
        # Hold duration
        hold_hours = (timestamp - position['entry_time']).total_seconds() / 3600
        
        trade = {
            **position,  # Includes exchange='MEXC', mode='backtest'
            'exit_price': actual_price,
            'exit_fee': exit_fee,
            'exit_time': timestamp,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'hold_hours': hold_hours,
            'exit_reason': reason,
        }
        
        self.closed_trades.append(trade)
        self.capital += net_proceeds
        
        print(f"  📉 SELL: {position['amount']:.4f} {symbol} @ ${actual_price:.4f}")
        print(f"     P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%) | Hold: {hold_hours:.1f}h")
        
        return True
    
    def run_backtest(self, data, strategy_func):
        """
        Run backtest on historical data
        
        Args:
            data: DataFrame with OHLCV data
            strategy_func: Function that returns 'BUY', 'SELL', or None
        """
        print(f"Starting backtest on {len(data)} candles...\n")
        
        for i, row in data.iterrows():
            signal = strategy_func(data, i)
            
            if signal == 'BUY':
                # Calculate position size (use 95% of available capital to account for fees)
                available = self.capital * 0.95
                amount = available / (row['close'] * (1 + self.slippage + self.taker_fee))
                
                self.open_position(
                    symbol=row.get('symbol', 'UNKNOWN'),
                    entry_price=row['close'],
                    amount=amount,
                    timestamp=row['timestamp'],
                    reason=f"Strategy signal: {signal}"
                )
            
            elif signal == 'SELL':
                self.close_position(
                    symbol=row.get('symbol', 'UNKNOWN'),
                    exit_price=row['close'],
                    timestamp=row['timestamp'],
                    reason=f"Strategy signal: {signal}"
                )
        
        # Close any remaining positions at end
        if self.positions:
            print(f"\n⚠️ Closing {len(self.positions)} remaining positions...")
            for pos in self.positions[:]:  # Copy list
                last_price = data.iloc[-1]['close']
                self.close_position(
                    pos['symbol'],
                    last_price,
                    data.iloc[-1]['timestamp'],
                    reason="End of backtest"
                )
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
        if not self.closed_trades:
            print("No trades to report")
            return None
        
        df = pd.DataFrame(self.closed_trades)
        
        # Calculate metrics
        total_trades = len(df)
        winners = df[df['pnl'] > 0]
        losers = df[df['pnl'] < 0]
        
        win_rate = (len(winners) / total_trades) * 100 if total_trades > 0 else 0
        avg_win = winners['pnl'].mean() if len(winners) > 0 else 0
        avg_loss = losers['pnl'].mean() if len(losers) > 0 else 0
        
        total_pnl = df['pnl'].sum()
        roi = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        # Sharpe ratio (simplified)
        returns = df['pnl_pct'] / 100
        sharpe = (returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() > 0 else 0
        
        report = {
            'strategy': self.strategy_name,
            'exchange': self.exchange,  # MEXC
            'mode': self.mode,          # backtest
            'backtest_date': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_pnl': total_pnl,
            'roi_pct': roi,
            'total_trades': total_trades,
            'winning_trades': len(winners),
            'losing_trades': len(losers),
            'win_rate_pct': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'risk_reward_ratio': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'sharpe_ratio': sharpe,
            'avg_hold_hours': df['hold_hours'].mean(),
            'total_fees_paid': df['entry_fee'].sum() + df['exit_fee'].sum(),
            'fee_structure': {
                'maker': f"{self.maker_fee*100:.3f}%",
                'taker': f"{self.taker_fee*100:.3f}%",
            },
        }
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"MEXC BACKTEST RESULTS - {self.strategy_name}")
        print(f"{'='*80}")
        print(f"Exchange: {self.exchange}")
        print(f"Mode: {self.mode}")
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Total P&L: ${total_pnl:,.2f}")
        print(f"ROI: {roi:.2f}%")
        print(f"Sharpe Ratio: {sharpe:.2f}")
        print(f"Risk/Reward: {report['risk_reward_ratio']:.2f}:1")
        print(f"Total Fees: ${report['total_fees_paid']:.2f}")
        print(f"{'='*80}\n")
        
        return report
    
    def save_results(self, output_dir='backtest_results'):
        """Save backtest results to JSON and CSV"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save report as JSON
        report = self.generate_report()
        if report:
            json_file = os.path.join(output_dir, f"{self.strategy_name}_mexc_{timestamp}_report.json")
            with open(json_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"✅ Report saved: {json_file}")
        
        # Save trades as CSV
        if self.closed_trades:
            df = pd.DataFrame(self.closed_trades)
            csv_file = os.path.join(output_dir, f"{self.strategy_name}_mexc_{timestamp}_trades.csv")
            df.to_csv(csv_file, index=False)
            print(f"✅ Trades saved: {csv_file}")
        
        return report


# Example usage
if __name__ == "__main__":
    # Load sample data
    data_file = 'data/mexc_history/BTC_USDT_1h_12m.csv'
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print(f"   Run: python download_mexc_history.py first")
        sys.exit(1)
    
    df = pd.read_csv(data_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['symbol'] = 'BTC/USDT'
    
    # Simple example strategy (SMA crossover)
    def sma_strategy(data, i):
        if i < 50:
            return None
        
        sma_20 = data['close'].iloc[i-20:i].mean()
        sma_50 = data['close'].iloc[i-50:i].mean()
        
        prev_sma_20 = data['close'].iloc[i-21:i-1].mean()
        prev_sma_50 = data['close'].iloc[i-51:i-1].mean()
        
        # Golden cross
        if sma_20 > sma_50 and prev_sma_20 <= prev_sma_50:
            return 'BUY'
        
        # Death cross
        if sma_20 < sma_50 and prev_sma_20 >= prev_sma_50:
            return 'SELL'
        
        return None
    
    # Run backtest
    engine = MEXCBacktestEngine('SMA_Crossover', initial_capital=1000)
    engine.run_backtest(df, sma_strategy)
    engine.save_results()
