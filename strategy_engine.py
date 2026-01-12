"""
CryptoBots V3 - Strategy Engine
Coordinates multiple strategies, manages positions, and executes trades.
"""

import ccxt
from typing import Dict, List, Optional
from datetime import datetime
from strategies import BuyDipStrategy, TakeProfitStrategy, TrendFollowingStrategy
from config_manager import ConfigManager
from health_monitor import HealthMonitor


class StrategyEngine:
    """
    Core trading engine that coordinates strategies and executes trades.
    Integrates with health monitoring and risk management.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the strategy engine.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.health_monitor = None
        self.exchange = None
        
        # Initialize strategies
        self.strategies = {
            'buy_dip': BuyDipStrategy(self.config.get_strategy_config('buy_dip')),
            'take_profit': TakeProfitStrategy(self.config.get_strategy_config('take_profit')),
            'trend_following': TrendFollowingStrategy(self.config.get_strategy_config('trend_following'))
        }
        
        # Trading state
        self.positions = []
        self.pending_orders = []
        self.is_running = False
        
        # Initialize exchange and health monitor
        self._init_exchange()
        self._init_health_monitor()
    
    def _init_exchange(self):
        """Initialize exchange connection."""
        exchange_config = self.config.get('exchange', {})
        exchange_name = exchange_config.get('name', 'binance')
        
        try:
            exchange_class = getattr(ccxt, exchange_name)
            
            config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
            
            api_key = exchange_config.get('api_key')
            api_secret = exchange_config.get('api_secret')
            
            if api_key and api_secret:
                config['apiKey'] = api_key
                config['secret'] = api_secret
            
            if exchange_config.get('testnet', False):
                config['options']['sandboxMode'] = True
            
            self.exchange = exchange_class(config)
            print(f"✅ Initialized {exchange_name} connection")
            
        except Exception as e:
            print(f"❌ Failed to initialize exchange: {e}")
            self.exchange = None
    
    def _init_health_monitor(self):
        """Initialize health monitoring."""
        exchange_config = self.config.get('exchange', {})
        
        self.health_monitor = HealthMonitor(
            exchange_id=exchange_config.get('name', 'binance'),
            api_key=exchange_config.get('api_key'),
            api_secret=exchange_config.get('api_secret')
        )
    
    def get_market_data(self, symbol: str) -> Dict:
        """
        Fetch current market data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            
        Returns:
            Dictionary with price, volume, 24h high/low, etc.
        """
        if not self.exchange:
            return {}
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=250)
            
            # Extract prices for MA calculation
            prices = [candle[4] for candle in ohlcv]  # Close prices
            
            return {
                'symbol': symbol,
                'current_price': ticker['last'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'volume_24h': ticker['quoteVolume'],
                'prices': prices,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"⚠️ Failed to fetch market data for {symbol}: {e}")
            return {}
    
    def check_strategies(self, symbol: str) -> List[Dict]:
        """
        Check all enabled strategies for signals.
        
        Args:
            symbol: Trading pair to check
            
        Returns:
            List of signals from strategies
        """
        signals = []
        market_data = self.get_market_data(symbol)
        
        if not market_data:
            return signals
        
        for strategy_name, strategy in self.strategies.items():
            if not strategy.is_enabled():
                continue
            
            signal = strategy.generate_signal(market_data)
            
            if signal:
                signals.append({
                    'strategy': strategy_name,
                    'signal': signal,
                    'symbol': symbol,
                    'price': market_data['current_price'],
                    'timestamp': datetime.now()
                })
        
        return signals
    
    def execute_trade(self, signal: Dict, balance: float) -> Optional[Dict]:
        """
        Execute a trade based on signal.
        
        Args:
            signal: Signal dictionary from strategy
            balance: Available balance for trading
            
        Returns:
            Trade result or None if failed
        """
        if not self.exchange:
            print("❌ No exchange connection")
            return None
        
        strategy_name = signal['strategy']
        strategy = self.strategies.get(strategy_name)
        
        if not strategy:
            return None
        
        symbol = signal['symbol']
        price = signal['price']
        side = signal['signal'].lower()  # 'buy' or 'sell'
        
        # Calculate position size
        position_size = strategy.calculate_position_size(balance, price)
        
        if position_size <= 0:
            print(f"⚠️ Invalid position size: {position_size}")
            return None
        
        try:
            # Execute order (paper trading mode for now)
            order = {
                'id': f"PAPER_{datetime.now().timestamp()}",
                'symbol': symbol,
                'side': side,
                'type': 'market',
                'amount': position_size,
                'price': price,
                'cost': position_size * price,
                'timestamp': datetime.now(),
                'strategy': strategy_name,
                'status': 'closed'
            }
            
            print(f"✅ Executed {side.upper()} order: {position_size:.6f} @ ${price:,.2f}")
            
            # Record trade
            strategy.add_trade({
                'symbol': symbol,
                'side': side,
                'price': price,
                'amount': position_size,
                'cost': position_size * price,
                'pnl': 0  # Calculate on exit
            })
            
            return order
            
        except Exception as e:
            print(f"❌ Trade execution failed: {e}")
            return None
    
    def manage_positions(self):
        """Check and manage existing positions."""
        for position in self.positions[:]:  # Copy to allow removal
            symbol = position['symbol']
            market_data = self.get_market_data(symbol)
            
            if not market_data:
                continue
            
            current_price = market_data['current_price']
            
            # Get the strategy that opened this position
            strategy_name = position.get('strategy')
            strategy = self.strategies.get(strategy_name)
            
            if not strategy:
                continue
            
            # Check exit conditions
            should_exit = strategy.check_exit_conditions(position, current_price)
            
            if should_exit:
                self._close_position(position, current_price, 'Exit condition met')
    
    def _close_position(self, position: Dict, current_price: float, reason: str):
        """
        Close a position and calculate P&L.
        
        Args:
            position: Position dictionary
            current_price: Current market price
            reason: Reason for closing
        """
        entry_price = position['entry_price']
        amount = position['amount']
        
        pnl = (current_price - entry_price) * amount
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        
        print(f"🔄 Closing position: {position['symbol']}")
        print(f"   Entry: ${entry_price:,.2f} | Exit: ${current_price:,.2f}")
        print(f"   P&L: ${pnl:+,.2f} ({pnl_percent:+.2f}%)")
        print(f"   Reason: {reason}")
        
        # Update trade history with P&L
        strategy = self.strategies.get(position['strategy'])
        if strategy:
            strategy.add_trade({
                'symbol': position['symbol'],
                'side': 'sell',
                'price': current_price,
                'amount': amount,
                'cost': current_price * amount,
                'pnl': pnl
            })
        
        # Remove position
        if position in self.positions:
            self.positions.remove(position)
    
    def get_strategy(self, name: str):
        """Get strategy by name."""
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> Dict:
        """Get all strategies."""
        return self.strategies
    
    def get_positions(self) -> List[Dict]:
        """Get current open positions."""
        return self.positions.copy()
    
    def get_performance_summary(self) -> Dict:
        """
        Get overall performance across all strategies.
        
        Returns:
            Dictionary with total trades, P&L, win rate, etc.
        """
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        total_pnl = 0.0
        
        for strategy in self.strategies.values():
            metrics = strategy.get_performance_metrics()
            total_trades += metrics['total_trades']
            winning_trades += metrics['winning_trades']
            losing_trades += metrics['losing_trades']
            total_pnl += metrics['total_pnl']
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0.0,
            'total_pnl': total_pnl,
            'avg_pnl_per_trade': total_pnl / total_trades if total_trades > 0 else 0.0,
            'open_positions': len(self.positions)
        }
    
    def run_health_check(self) -> bool:
        """
        Run health check and determine if trading should continue.
        
        Returns:
            True if healthy, False if critical issues detected
        """
        if not self.health_monitor:
            return True
        
        self.health_monitor.run_full_check(debug=False)
        return not self.health_monitor.should_stop_trading()
    
    def start(self):
        """Start the trading engine."""
        self.is_running = True
        print("🚀 Strategy Engine started")
    
    def stop(self):
        """Stop the trading engine."""
        self.is_running = False
        print("🛑 Strategy Engine stopped")
