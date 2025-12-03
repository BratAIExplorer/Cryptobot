import time
import pandas as pd
from datetime import datetime, timedelta
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
        
        # Circuit Breaker (Safety Feature)
        self.circuit_breaker = {
            'consecutive_errors': 0,
            'max_errors': 10,
            'is_open': False,
            'last_error_time': None
        }
        
        # Watchdog (Safety Feature)
        self.watchdog = {
            'last_check': datetime.now(),
            'check_interval_minutes': 10
        }

    def add_bot(self, strategy_config):
        """Add a bot configuration"""
        self.active_bots.append(strategy_config)
        print(f"Bot added: {strategy_config['name']}")

    def check_circuit_breaker(self):
        """Check if circuit breaker should be triggered (Safety Feature)"""
        if self.circuit_breaker['is_open']:
            print("🔴 CIRCUIT BREAKER OPEN - Bot is paused")
            return False
        
        if self.circuit_breaker['consecutive_errors'] >= self.circuit_breaker['max_errors']:
            self.circuit_breaker['is_open'] = True
            self.notifier.send_message("🔴 CIRCUIT BREAKER OPEN - Bot paused after 10 consecutive errors")
            self.is_running = False
            return False
        
        return True
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker after successful trade"""
        if self.circuit_breaker['consecutive_errors'] > 0:
            self.circuit_breaker['consecutive_errors'] = 0
    
    def check_watchdog(self):
        """Check for no-sell condition (Safety Feature)"""
        now = datetime.now()
        if (now - self.watchdog['last_check']).seconds < self.watchdog['check_interval_minutes'] * 60:
            return  # Not time to check yet
        
        self.watchdog['last_check'] = now
        
        # Check recent trades
        trades = self.logger.get_trades()
        if trades.empty:
            return
        
        # Convert timestamp to datetime if it's a string
        trades['timestamp'] = pd.to_datetime(trades['timestamp'])
        recent_trades = trades[trades['timestamp'] > now - timedelta(hours=6)]
        
        buys = len(recent_trades[recent_trades['side'] == 'BUY'])
        sells = len(recent_trades[recent_trades['side'] == 'SELL'])
        
        if buys > 20 and sells == 0:
            self.notifier.send_message(f"🚨 WATCHDOG ALERT: {buys} buys with 0 sells in last 6 hours!")
            print(f"⚠️ WATCHDOG: {buys} buys, 0 sells in 6h")
        elif buys > sells * 10 and sells > 0:
            self.notifier.send_message(f"⚠️ WATCHDOG: High buy/sell ratio: {buys}/{sells}")

    def start(self):
        """Start the main loop"""
        self.is_running = True
        print(f"Engine started in {self.mode} mode")
        
        # Update bot status on start for ALL bots
        for bot in self.active_bots:
            total_pnl = self.logger.get_pnl_summary(bot['name'])
            # Force 50k initial balance
            wallet_balance = self.logger.get_wallet_balance(bot['name'], initial_balance=50000.0)
            print(f"[STARTUP] Updating {bot['name']}: PnL=${total_pnl}, Balance=${wallet_balance}")
            self.logger.update_bot_status(bot['name'], 'RUNNING', 0, total_pnl, wallet_balance)
        
        while self.is_running:
            # Check circuit breaker
            if not self.check_circuit_breaker():
                break
            
            # Check watchdog
            self.check_watchdog()
            
            if not self.risk_manager.can_trade():
                print("Outside trading hours. Sleeping...")
                time.sleep(120)  # Increased to 120s to avoid API limits
                continue

            for bot in self.active_bots:
                # --- Heartbeat & Status Update ---
                # 1. Get stats
                all_trades = self.logger.get_trades()
                if not all_trades.empty:
                    # Filter trades for this specific bot strategy
                    bot_trades = all_trades[all_trades['strategy'] == bot['name']]
                    total_trades = len(bot_trades)
                else:
                    total_trades = 0
                
                total_pnl = self.logger.get_pnl_summary(bot['name'])
                wallet_balance = self.logger.get_wallet_balance(bot['name'], initial_balance=bot.get('initial_balance', 50000))
                
                # 2. Update DB
                self.logger.update_bot_status(bot['name'], 'RUNNING', total_trades, total_pnl, wallet_balance)
                
                # 3. Process Strategy
                self.process_bot(bot)
            
            time.sleep(120)  # Loop interval - 60s to avoid rate limits

    def stop(self):
        self.is_running = False
        print("Engine stopped")

    def process_bot(self, bot):
        """Execute logic for a single bot configuration (can be multiple symbols)"""
        symbols = bot.get('symbols', [bot.get('symbol')])
        strategy_type = bot['type']
        
        for symbol in symbols:
            try:
                # Fetch data
                df = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                if df.empty:
                    continue

                current_price = df['close'].iloc[-1]
                rsi = calculate_rsi(df['close']).iloc[-1]
                
                # Check for SELL signals first (FIFO)
                open_positions = self.logger.get_open_positions(symbol)
                if not open_positions.empty:
                    oldest_position = open_positions.iloc[0]
                    buy_price = oldest_position['buy_price']
                    position_id = oldest_position['id']
                    buy_timestamp = oldest_position['buy_timestamp']
                    
                    # Calculate position age
                    try:
                        buy_time = pd.to_datetime(buy_timestamp)
                        position_age_hours = (datetime.now() - buy_time).total_seconds() / 3600
                    except:
                        position_age_hours = 0
                    
                    # Get strategy-specific settings
                    tp_pct = bot.get('take_profit_pct', 0.03)
                    sl_pct = bot.get('stop_loss_pct', 0.05)
                    max_hold_hours = bot.get('max_hold_hours', 24)
                    
                    # Calculate profit %
                    profit_pct = (current_price - buy_price) / buy_price
                    
                    sell_reason = None
                    
                    # Priority 1: Stop Loss (always check first)
                    if current_price <= buy_price * (1 - sl_pct):
                        sell_reason = f"SL Hit (-{sl_pct*100:.1f}%)"
                    
                    # Priority 2: Strategy Specific Exits
                    elif strategy_type == 'Buy-the-Dip':
                        # Tiered exits: 50% @ 5%, 25% @ 7%, 25% @ 10%
                        if profit_pct >= 0.10:
                            sell_reason = f"TP3 Hit (+10%)"
                        elif profit_pct >= 0.07:
                            sell_reason = f"TP2 Hit (+7%)"
                        elif profit_pct >= 0.05:
                            sell_reason = f"TP1 Hit (+5%)"
                        # Emergency exit after 120 days
                        elif position_age_hours >= (120 * 24) and profit_pct >= -0.05:
                            sell_reason = f"Time Exit 120d ({profit_pct*100:.1f}%)"
                            
                    elif strategy_type == 'Hyper-Scalper':
                        # Scalper should exit within 30 minutes if profitable
                        if position_age_hours >= 0.5 and profit_pct > 0.001:
                            sell_reason = f"Scalp Exit +{profit_pct*100:.2f}% ({position_age_hours*60:.0f}min)"
                        # Standard TP
                        elif current_price >= buy_price * (1 + tp_pct):
                            sell_reason = f"TP Hit (+{tp_pct*100:.1f}%)"
                    
                    # Priority 3: Standard Take Profit (for other strategies)
                    elif current_price >= buy_price * (1 + tp_pct):
                        sell_reason = f"TP Hit (+{tp_pct*100:.1f}%)"
                    
                    # Priority 4: Time-based exit for aging positions
                    elif position_age_hours >= max_hold_hours:
                        sell_reason = f"Time Exit ({position_age_hours:.1f}h old, {profit_pct*100:.1f}%)"
                    
                    # Priority 5: Break-even exit for stuck positions (after 6 hours)
                    elif position_age_hours >= 6 and profit_pct >= 0.001:
                         sell_reason = f"Break-Even Exit ({position_age_hours:.1f}h old)"
                    
                    if sell_reason:
                        print(f"[{bot['name']}] Selling {symbol}: {sell_reason}")
                        self.execute_trade(bot, symbol, 'SELL', current_price, rsi, position_id=position_id)
                        continue  # Skip buy check after selling
                
                # Strategy Logic for BUY signals
                signal = None
                if strategy_type == 'DCA':
                    if rsi < bot.get('rsi_limit', 40):
                        signal = 'BUY'
                
                elif strategy_type == 'Hyper-Scalper':
                    rsi_3 = calculate_rsi(df['close'], period=3).iloc[-1]
                    if rsi_3 < bot.get('rsi_limit', 10):
                        signal = 'BUY'
                        
                elif strategy_type == 'Volatility Hunter':
                    last_open = df['open'].iloc[-1]
                    last_close = df['close'].iloc[-1]
                    pct_change = (last_close - last_open) / last_open
                    if pct_change > bot.get('volatility_threshold', 0.02):
                        signal = 'BUY'

                elif strategy_type == 'SMA':
                    sma_20 = calculate_sma(df['close'], period=20).iloc[-1]
                    sma_50 = calculate_sma(df['close'], period=50).iloc[-1]
                    if sma_20 > sma_50:
                        signal = 'BUY'

                elif strategy_type == 'Grid':
                    # Simple Grid/Mean Reversion: Buy if price is 3% below SMA 50
                    sma_50 = calculate_sma(df['close'], period=50).iloc[-1]
                    if current_price < sma_50 * 0.97:
                        signal = 'BUY'
                
                elif strategy_type == 'Buy-the-Dip':
                    # Buy on 8-10% dips from 24h high
                    recent_high = df['high'].rolling(window=24).max().iloc[-1]
                    drop_pct = ((current_price - recent_high) / recent_high)
                    
                    if -0.15 <= drop_pct <= -0.04:  # Widened to 4-15% drop
                        signal = 'BUY'

                # Execute BUY
                if signal == 'BUY':
                    self.execute_trade(bot, symbol, 'BUY', current_price, rsi)
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                self.circuit_breaker['consecutive_errors'] += 1
                self.circuit_breaker['last_error_time'] = datetime.now()

    def execute_trade(self, bot, symbol, side, price, rsi, position_id=None):
        """Execute a trade with FIFO position management"""
        max_exposure = bot.get('max_exposure_per_coin', 2000)
        trade_amount_usd = bot['amount']
        
        if side == 'BUY':
            # Check current exposure (Issue #5 fix: per-strategy)
            current_exposure = self.logger.get_total_exposure(symbol, strategy=bot['name'])
            
            if current_exposure + trade_amount_usd > max_exposure:
                print(f"[SKIP] {symbol} exposure limit reached: ${current_exposure:.2f} / ${max_exposure}")
                return
            
            # Execute buy
            amount = trade_amount_usd / price
            
            if self.mode == 'paper':
                print(f"●BUY {symbol}● Price: ${price:.4f}, Amount: {amount:.4f}")
                
                # Open position (FIFO)
                position_id = self.logger.open_position(symbol, bot['name'], price, amount)
                
                # Log trade (with versioning)
                strategy_version = bot.get('version', '1.0')
                self.logger.log_trade(bot['name'], symbol, side, price, amount, rsi=rsi, position_id=position_id, engine_version='2.0', strategy_version=strategy_version)
                
                # Send Notification
                self.notifier.notify_trade(symbol, side, price, amount, reason=f"RSI: {rsi:.2f}")
                
                # Reset circuit breaker on successful trade
                self.reset_circuit_breaker()
                
                # Update bot status
                total_trades = len(self.logger.get_trades())
                total_pnl = self.logger.get_pnl_summary(bot['name'])
                wallet_balance = self.logger.get_wallet_balance(bot['name'], initial_balance=bot.get('initial_balance', 20000))
                self.logger.update_bot_status(bot['name'], 'RUNNING', total_trades, total_pnl, wallet_balance)
        
        elif side == 'SELL' and position_id:
            # Get position details
            open_positions = self.logger.get_open_positions(symbol)
            position = open_positions[open_positions['id'] == position_id].iloc[0]
            amount = position['amount']
            
            if self.mode == 'paper':
                print(f"●SELL {symbol}● Price: ${price:.4f}, Amount: {amount:.4f}")
                
                # Close position (FIFO)
                profit = self.logger.close_position(position_id, price)
                
                # Safety check: Handle case where position wasn't found
                if profit is None:
                    print(f"[WARNING] Skipping trade logging - position #{position_id} not found")
                    return  # Exit early, don't continue with logging/notification
                
                # Log trade (with versioning)
                strategy_version = bot.get('version', '1.0')
                self.logger.log_trade(bot['name'], symbol, side, price, amount, rsi=rsi, position_id=position_id, engine_version='2.0', strategy_version=strategy_version)
                
                # Send Notification
                profit_str = f"Profit: ${profit:.2f}" if profit is not None else "Profit: N/A (Error)"
                self.notifier.notify_trade(symbol, side, price, amount, reason=profit_str)
                
                # Reset circuit breaker on successful trade
                self.reset_circuit_breaker()
                
                # Update bot status
                total_trades = len(self.logger.get_trades())
                total_pnl = self.logger.get_pnl_summary(bot['name'])
                wallet_balance = self.logger.get_wallet_balance(bot['name'], initial_balance=bot.get('initial_balance', 20000))
                self.logger.update_bot_status(bot['name'], 'RUNNING', total_trades, total_pnl, wallet_balance)
