import time
import pandas as pd
from .exchange import ExchangeInterface
from .logger import TradeLogger
from .risk_manager import RiskManager
from .notifier import TelegramNotifier
from utils.indicators import calculate_rsi, calculate_sma

class TradingEngine:
    def __init__(self, mode='paper', telegram_config=None):
        self.mode = mode
        self.exchange = ExchangeInterface(mode)
        self.logger = TradeLogger()
        self.risk_manager = RiskManager()
        self.notifier = TelegramNotifier(
            token=telegram_config.get('token') if telegram_config else None,
            chat_id=telegram_config.get('chat_id') if telegram_config else None
        )
        self.active_bots = []
        self.is_running = False

    def add_bot(self, strategy_config):
        """Add a bot configuration"""
        self.active_bots.append(strategy_config)
        print(f"Bot added: {strategy_config['name']}")

    def start(self):
        """Start the main loop"""
        self.is_running = True
        print(f"Engine started in {self.mode} mode")
        
        while self.is_running:
            if not self.risk_manager.can_trade():
                print("Outside trading hours. Sleeping...")
                time.sleep(60)
                continue

            for bot in self.active_bots:
                self.process_bot(bot)
            
            time.sleep(10) # Loop interval

    def stop(self):
        self.is_running = False
        print("Engine stopped")

    def process_bot(self, bot):
        """Execute logic for a single bot configuration (can be multiple symbols)"""
        symbols = bot.get('symbols', [bot.get('symbol')]) # Handle both list and single (legacy)
        strategy_type = bot['type']
        
        for symbol in symbols:
            try:
                # Fetch data
                df = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                if df.empty:
                    continue

                current_price = df['close'].iloc[-1]
                
                # Calculate Indicators
                rsi = calculate_rsi(df['close']).iloc[-1]
                
                # Strategy Logic
                signal = None
                if strategy_type == 'DCA':
                    if rsi < bot.get('rsi_limit', 40):
                        signal = 'BUY'
                
                elif strategy_type == 'SMA':
                    # Placeholder for SMA logic
                    pass
                
                elif strategy_type == 'Grid':
                     # Placeholder for Grid logic
                     pass

                elif strategy_type == 'Hyper-Scalper':
                    # Aggressive RSI (Period 3)
                    rsi_3 = calculate_rsi(df['close'], period=3).iloc[-1]
                    if rsi_3 < bot.get('rsi_limit', 10):
                        signal = 'BUY'
                        
                elif strategy_type == 'Volatility Hunter':
                    # Check % change of last candle
                    last_open = df['open'].iloc[-1]
                    last_close = df['close'].iloc[-1]
                    pct_change = (last_close - last_open) / last_open
                    if pct_change > bot.get('volatility_threshold', 0.02):
                        signal = 'BUY'

                # Execute
                if signal == 'BUY':
                    self.execute_trade(bot, symbol, 'BUY', current_price, rsi)
                    
            except Exception as e:
                print(f"Error processing {symbol}: {e}")

    def execute_trade(self, bot, symbol, side, price, rsi):
        """Execute a trade (Paper or Live)"""
        amount = bot['amount'] / price
        
        if self.mode == 'paper':
            print(f"PAPER TRADE: {side} {symbol} @ {price}")
            self.logger.log_trade(bot['name'], symbol, side, price, amount, rsi=rsi)
            # Send Notification
            self.notifier.notify_trade(symbol, side, price, amount, reason=f"RSI: {rsi:.2f}")
        else:
            # Live execution would go here
            pass
