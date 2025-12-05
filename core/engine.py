import time
import pandas as pd
from datetime import datetime, timedelta
from .exchange import ExchangeInterface
from .logger import TradeLogger
from .risk_manager import RiskManager
from .notifier import TelegramNotifier
from utils.indicators import calculate_rsi, calculate_sma
from strategies.grid_strategy_v2 import GridStrategyV2

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
        
        # Watchdog (Safety Feature)
        self.watchdog = {
            'last_check': datetime.now(),
            'check_interval_minutes': 10
        }
        
        # No-activity monitoring
        self.last_trade_time = datetime.now()
        self.no_activity_alert_sent = False
        
        # Milestone tracking
        self.last_milestone = 0
        self.milestones = [100, 250, 500, 1000, 2500, 5000, 10000]
        
        # Rate limiting
        self.api_call_count = 0
        self.api_reset_time = datetime.now()
        self.max_api_calls_per_minute = 30  # Conservative limit
        
        # Strategy Instances (for stateful strategies like Grid)
        self.strategies = {}

    def add_bot(self, strategy_config):
        """Add a bot configuration"""
        self.active_bots.append(strategy_config)
        
        # Initialize strategy instance if needed
        if strategy_config['type'] == 'Grid':
            # Create a unique key for the strategy instance
            # Assuming Grid bot has one symbol per config for now
            symbol = strategy_config.get('symbols', [None])[0]
            if symbol:
                # Pass the full config, ensure symbol is set
                config = strategy_config.copy()
                config['symbol'] = symbol
                self.strategies[strategy_config['name']] = GridStrategyV2(config)
                
        print(f"Bot added: {strategy_config['name']}")

    def check_circuit_breaker(self):
        """Check if circuit breaker should be triggered (Persistent Safety Feature)"""
        # Check for auto-recovery first
        was_open = self.logger.get_circuit_breaker_status()['is_open']
        self.logger.check_circuit_breaker_auto_recovery(cooldown_minutes=30)
        
        # Get current status from database
        status = self.logger.get_circuit_breaker_status()
        
        if status['is_open']:
            # Send alert only on first trigger (not every loop)
            if not was_open or status['consecutive_errors'] >= 10:
                self.notifier.alert_circuit_breaker(status['consecutive_errors'])
            print("🔴 CIRCUIT BREAKER OPEN - Bot is paused (waiting for cooldown)")
            return False
        
        return True
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker after successful trade"""
        self.logger.reset_circuit_breaker()
    
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
        
        # Filter for Hyper-Scalper only (Grid and Dip bots are expected to accumulate)
        scalper_trades = recent_trades[recent_trades['strategy'].str.contains('Hyper-Scalper', case=False, na=False)]
        
        if scalper_trades.empty:
            return

        buys = len(scalper_trades[scalper_trades['side'] == 'BUY'])
        sells = len(scalper_trades[scalper_trades['side'] == 'SELL'])
        
        if buys > 20 and sells == 0:
            self.notifier.send_message(f"🚨 WATCHDOG ALERT (Scalper): {buys} buys with 0 sells in last 6 hours!")
            print(f"⚠️ WATCHDOG: {buys} buys, 0 sells in 6h")
        elif buys > sells * 10 and sells > 0:
            self.notifier.send_message(f"⚠️ WATCHDOG (Scalper): High buy/sell ratio: {buys}/{sells}")

    def start(self):
        """Start the main loop"""
        self.is_running = True
        print(f"Engine started in {self.mode} mode")
        
        # Send startup notification
        self.notifier.alert_service_restart()
        
        # Update bot status on start for ALL bots
        for bot in self.active_bots:
            total_pnl = self.logger.get_pnl_summary(bot['name'])
            # Force 50k initial balance
            wallet_balance = self.logger.get_wallet_balance(bot['name'], initial_balance=50000.0)
            print(f"[STARTUP] Updating {bot['name']}: PnL=${total_pnl}, Balance=${wallet_balance}")
            self.logger.update_bot_status(bot['name'], 'RUNNING', 0, total_pnl, wallet_balance)
        
        while self.is_running:
            # Check circuit breaker with auto-recovery
            if not self.check_circuit_breaker():
                print("⏸️  Circuit breaker paused. Waiting for auto-recovery...")
                time.sleep(60)  # Check every minute for auto-recovery
                continue
            
            # Check watchdog
            self.check_watchdog()
            
            # Clean up stuck positions
            self.cleanup_aged_positions()
            
            # Check max drawdown limit (Industry standard safety feature)
            total_pnl = self.logger.get_pnl_summary()  # All strategies combined
            current_equity = 50000 + total_pnl  # Initial balance + realized P&L
            can_trade, drawdown_pct = self.risk_manager.check_drawdown_limit(current_equity, self.logger)
            
            # Alert at 80% of max drawdown (warning)
            if drawdown_pct >= (self.risk_manager.max_drawdown_pct * 100 * 0.8) and drawdown_pct < (self.risk_manager.max_drawdown_pct * 100):
                self.notifier.alert_max_drawdown(
                    drawdown_pct, 
                    self.risk_manager.max_drawdown_pct * 100,
                    current_equity,
                    self.risk_manager.peak_equity
                )
            
            if not can_trade:
                # Send critical alert when max drawdown hit
                self.notifier.alert_max_drawdown(
                    drawdown_pct,
                    self.risk_manager.max_drawdown_pct * 100,
                    current_equity,
                    self.risk_manager.peak_equity
                )
                print(f"⏸️ Drawdown limit exceeded: {drawdown_pct:.1f}% (max: {self.risk_manager.max_drawdown_pct*100:.0f}%)")
                print(f"   Peak Equity: ${self.risk_manager.peak_equity:.2f} | Current: ${current_equity:.2f}")
                time.sleep(3600)  # Pause for 1 hour before rechecking
                continue
            
            if not self.risk_manager.can_trade():
                print("Outside trading hours. Sleeping...")
                time.sleep(120)
                continue
            
            # Check for no-activity (6 hour silence)
            self.check_no_activity()

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
                
                # Check for profit milestones
                self.check_profit_milestones(total_pnl)
                
                # 2. Update DB
                self.logger.update_bot_status(bot['name'], 'RUNNING', total_trades, total_pnl, wallet_balance)
                
                # 3. Process Strategy
                self.process_bot(bot)
            
            time.sleep(180)  # Loop interval - 180s for better rate limiting

    def stop(self):
        self.is_running = False
        print("Engine stopped")
    
    def check_no_activity(self):
        """Alert if bot hasn't traded in 6 hours"""
        trades = self.logger.get_trades()
        if trades.empty:
            return  # No trades yet, bot just started
        
        trades['timestamp'] = pd.to_datetime(trades['timestamp'])
        last_trade_time = trades['timestamp'].max()
        hours_since_trade = (datetime.now() - last_trade_time).total_seconds() / 3600
        
        if hours_since_trade >= 6 and not self.no_activity_alert_sent:
            self.notifier.alert_no_activity(int(hours_since_trade))
            self.no_activity_alert_sent = True
        elif hours_since_trade < 6:
            self.no_activity_alert_sent = False  # Reset flag
    
    def check_profit_milestones(self, total_pnl):
        """Check and alert on profit milestones"""
        if total_pnl <= 0:
            return
        
        for milestone in self.milestones:
            if total_pnl >= milestone and self.last_milestone < milestone:
                self.notifier.alert_profit_milestone(milestone, total_pnl)
                self.last_milestone = milestone
                break
    
    def cleanup_aged_positions(self):
        """Automatically force-close positions that are older than 3x their max hold time"""
        # Strategy max hold times (in hours)
        max_hold_times = {
            'Hyper-Scalper Bot': 0.5,  # 30 minutes
            'Buy-the-Dip Strategy': 2880,  # 120 days
            'SMA Trend Bot': 24  # 24 hours
        }
        
        open_positions = self.logger.get_open_positions()
        if open_positions.empty:
            return
        
        for _, position in open_positions.iterrows():
            strategy = position['strategy']
            symbol = position['symbol']
            position_id = position['id']
            buy_timestamp = pd.to_datetime(position['buy_timestamp'])
            
            # Calculate position age
            age_hours = (datetime.now() - buy_timestamp).total_seconds() / 3600
            max_hold = max_hold_times.get(strategy, 24)
            
            # Force close if older than 3x max hold time (severe aging)
            if age_hours > (max_hold * 3):
                print(f"[AUTO-CLEANUP] Force-closing aged position #{position_id}: {symbol} ({age_hours:.1f}h old, max: {max_hold}h)")
                
                try:
                    # Get current price
                    df = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=1)
                    if not df.empty:
                        current_price = df['close'].iloc[-1]
                        
                        # Close position with exit RSI
                        profit = self.logger.close_position(position_id, current_price, exit_rsi=rsi)
                        if profit is not None:
                            print(f"[AUTO-CLEANUP] Position #{position_id} closed with profit: ${profit:.2f}")
                            
                            # Log the trade with fee
                            amount = position['amount']
                            fee = current_price * amount * 0.001  # 0.1% fee
                            self.logger.log_trade(strategy, symbol, 'SELL', current_price, amount, 
                                                fee=fee, rsi=rsi, position_id=position_id, engine_version='2.0')
                except Exception as e:
                    print(f"[AUTO-CLEANUP] Error closing aged position #{position_id}: {e}")


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
                
                # --- SPECIAL HANDLING FOR GRID BOT ---
                if strategy_type == 'Grid':
                    strategy_instance = self.strategies.get(bot['name'])
                    if strategy_instance:
                        open_positions = self.logger.get_open_positions(symbol)
                        signal = strategy_instance.get_signal(current_price, open_positions)
                        
                        if signal:
                            if signal['side'] == 'SELL':
                                print(f"[{bot['name']}] Grid SELL Signal: {signal['reason']}")
                                self.execute_trade(bot, symbol, 'SELL', current_price, rsi, position_id=signal['position_id'])
                            elif signal['side'] == 'BUY':
                                print(f"[{bot['name']}] Grid BUY Signal: {signal['reason']}")
                                self.execute_trade(bot, symbol, 'BUY', current_price, rsi, reason=signal['reason'])
                        continue # Skip standard logic for Grid
                
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
                        # Minimum 0.75% to cover 0.2-0.4% round-trip fees
                        if position_age_hours >= 0.5 and profit_pct >= 0.0075:  # 0.75% minimum
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
                    # Raised to 0.75% to cover fees
                    elif position_age_hours >= 6 and profit_pct >= 0.0075:  # 0.75% minimum
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
                error_count = self.logger.increment_circuit_breaker_errors()
                if error_count >= 10:
                    self.notifier.send_message(f"🔴 CIRCUIT BREAKER TRIGGERED - {error_count} consecutive errors. Auto-recovery in 30 min.")
                    print(f"⚠️  Circuit breaker triggered after {error_count} errors")

    def execute_trade(self, bot, symbol, side, price, rsi, position_id=None, reason=None):
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
                
                # Open position (FIFO) with entry RSI
                position_id = self.logger.open_position(symbol, bot['name'], price, amount, entry_rsi=rsi)
                
                # Calculate fee (0.1% Binance standard)
                fee = price * amount * 0.001
                
                # Log trade (with versioning and fee)
                strategy_version = bot.get('version', '1.0')
                self.logger.log_trade(bot['name'], symbol, side, price, amount, fee=fee, rsi=rsi, 
                                    position_id=position_id, engine_version='2.0', strategy_version=strategy_version)
                
                # Send Notification
                trade_reason = reason if reason else f"RSI: {rsi:.2f}"
                self.notifier.notify_trade(symbol, side, price, amount, reason=trade_reason)
                
                # Reset circuit breaker on successful trade
                self.reset_circuit_breaker()
                
                # Update bot status with accurate per-strategy metrics
                all_trades = self.logger.get_trades()
                bot_trades = all_trades[all_trades['strategy'] == bot['name']] if not all_trades.empty else []
                total_trades = len(bot_trades)
                total_pnl = self.logger.get_pnl_summary(bot['name'])
                wallet_balance = self.logger.get_wallet_balance(bot['name'], initial_balance=bot.get('initial_balance', 50000))
                self.logger.update_bot_status(bot['name'], 'RUNNING', total_trades, total_pnl, wallet_balance)
        
        elif side == 'SELL' and position_id:
            # Get position details
            open_positions = self.logger.get_open_positions(symbol)
            
            # Safety check: ensure position exists
            if open_positions.empty or position_id not in open_positions['id'].values:
                print(f"[SKIP] Position #{position_id} already closed or not found for {symbol}")
                return  # Exit early without logging error to circuit breaker
            
            position = open_positions[open_positions['id'] == position_id].iloc[0]
            amount = position['amount']
            
            if self.mode == 'paper':
                print(f"●SELL {symbol}● Price: ${price:.4f}, Amount: {amount:.4f}")
                
                # Double-check position still exists (race condition protection)
                # Refresh positions right before closing
                refresh_positions = self.logger.get_open_positions(symbol)
                if refresh_positions.empty or position_id not in refresh_positions['id'].values:
                    print(f"[SKIP] Position #{position_id} was closed between check and execution")
                    return
                
                # Close position (FIFO) with exit RSI
                profit = self.logger.close_position(position_id, price, exit_rsi=rsi)
                
                # Safety check: Handle case where position wasn't found
                if profit is None:
                    print(f"[SKIP] Position #{position_id} already processed")
                    return  # Exit early, don't continue with logging/notification
                
                # Calculate fee (0.1% Binance standard)
                fee = price * amount * 0.001
                
                # Alert on large losses
                if profit < -50:  # Loss greater than $50
                    profit_pct = (profit / position['cost']) * 100
                    self.notifier.alert_large_loss(symbol, abs(profit), abs(profit_pct))
                
                # Update last trade time for no-activity monitoring
                self.last_trade_time = datetime.now()
                
                # Log trade (with versioning and fee)
                strategy_version = bot.get('version', '1.0')
                self.logger.log_trade(bot['name'], symbol, side, price, amount, fee=fee, rsi=rsi, 
                                    position_id=position_id, engine_version='2.0', strategy_version=strategy_version)
                
                # Send Notification
                profit_str = f"Profit: ${profit:.2f}"
                self.notifier.notify_trade(symbol, side, price, amount, reason=profit_str)
                
                # Reset circuit breaker on successful trade
                self.reset_circuit_breaker()
                
                # Update bot status with accurate per-strategy metrics
                all_trades = self.logger.get_trades()
                bot_trades = all_trades[all_trades['strategy'] == bot['name']] if not all_trades.empty else []
                total_trades = len(bot_trades)
                total_pnl = self.logger.get_pnl_summary(bot['name'])
                wallet_balance = self.logger.get_wallet_balance(bot['name'], initial_balance=bot.get('initial_balance', 50000))
                self.logger.update_bot_status(bot['name'], 'RUNNING', total_trades, total_pnl, wallet_balance)
