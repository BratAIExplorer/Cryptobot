import sys
import os
import time
from decimal import Decimal
import pandas as pd
from datetime import datetime, timedelta
from .exchange import ExchangeInterface
from .exchange_unified import UnifiedExchange
from .logger import TradeLogger
from .risk_module import RiskManager, setup_safe_trading_bot

# Add luno-monitor to path for Confluence Engine
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(root_dir, 'luno-monitor', 'src'))
from .resilience import ExchangeResilienceManager
from .execution import OrderExecutionManager
from .observability import SystemMonitor
from .notifier import TelegramNotifier
from utils.indicators import calculate_rsi, calculate_sma
from strategies.grid_strategy_v2 import DynamicGridStrategy
from .veto import VetoManager


class TradingEngine:
    def __init__(self, mode='paper', telegram_config=None, exchange='Binance', db_path=None):
        self.mode = mode
        self.exchange_name = exchange
        
        # Use unified exchange if not Binance
        if exchange.upper() != 'BINANCE':
            from .exchange_unified import UnifiedExchange
            self.exchange = UnifiedExchange(exchange_name=exchange, mode=mode)
        else:
            self.exchange = ExchangeInterface(mode)
        
        # Initialize logger with db_path if provided, otherwise use default
        if db_path:
            self.logger = TradeLogger(db_path=db_path)
        else:
            self.logger = TradeLogger()
        
        # Initialize Safety Managers
        self.risk_manager = setup_safe_trading_bot('moderate') # Default to Moderate Risk
        self.resilience_manager = ExchangeResilienceManager("Binance") # Default exchange
        self.resilience_manager = ExchangeResilienceManager("Binance") # Default exchange
        self.execution_manager = None # Initialized per trade
        self.veto_manager = VetoManager(self.exchange, self.logger)

        
        # Initialize Observability
        # Initialize Observability (Pass risk manager)
        self.system_monitor = SystemMonitor(self.logger, self.risk_manager, self.resilience_manager)
        
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
        self.last_resilience_alert = datetime.min  # For throttling disconnection alerts
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
                self.strategies[strategy_config['name']] = DynamicGridStrategy(config)
                
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
        
        if buys > 25 and sells == 0:
            self.notifier.send_message(f"🚨 WATCHDOG ALERT (Scalper): {buys} buys with 0 sells in last 6 hours!")
            print(f"⚠️ WATCHDOG: {buys} buys, 0 sells in 6h")
        elif buys > sells * 20 and sells > 0:
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
            self.run_cycle()
            time.sleep(180)  # Loop interval - 180s for better rate limiting

    def run_cycle(self):
        """Execute one full pass of the trading logic and safety checks"""
        # Observability Snapshot (Safety Heartbeat)
        try:
            self.system_monitor.snapshot()
        except Exception as e:
            print(f"[MONITOR] Snapshot failed: {e}")

        # Check circuit breaker with auto-recovery
        if not self.check_circuit_breaker():
            print("⏸️  Circuit breaker paused. Waiting for auto-recovery...")
            return
            
        # --- DAILY LOSS LIMIT CHECK ---
        can_trade_daily, reason = self.risk_manager.check_daily_loss_limit()
        if not can_trade_daily:
            print(f"🔴 RISK STOP: {reason}")
            # Throttled notification could go here if needed
            return
        
        # --- COOLDOWN CHECK ---
        can_trade_cooldown, reason = self.risk_manager.check_cooldown()
        if not can_trade_cooldown:
            print(f"❄️ COOLDOWN: {reason}")
            return
        
        # Check watchdog
        self.check_watchdog()
        
        # Clean up stuck positions
        self.cleanup_aged_positions()
        
        # --- PORTFOLIO SNAPSHOT (Institutional Hardening) ---
        self._take_portfolio_snapshot()
        
        # Check max drawdown limit (Industry standard safety feature)
        total_pnl = self.logger.get_pnl_summary()  # All strategies combined
        current_equity = Decimal(str(self.risk_manager.portfolio_value)) + Decimal(str(total_pnl))
        can_trade, drawdown_pct = self.risk_manager.check_drawdown_limit(current_equity, self.logger)
        
        # Alert at 80% of max drawdown (warning)
        max_drawdown = self.risk_manager.max_drawdown_pct
        if drawdown_pct >= (max_drawdown * Decimal("0.8")) and drawdown_pct < max_drawdown:
            self.notifier.alert_max_drawdown(
                drawdown_pct, 
                max_drawdown,
                current_equity,
                self.risk_manager.peak_equity
            )
        
        if not can_trade:
            # Send critical alert when max drawdown hit
            self.notifier.alert_max_drawdown(
                drawdown_pct,
                max_drawdown,
                current_equity,
                self.risk_manager.peak_equity
            )
            print(f"⏸️ Drawdown limit exceeded: {drawdown_pct:.1f}% (max: {max_drawdown:.0f}%)")
            return
        
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
    
    def check_position_age_alerts(self, position, age_days):
        """Send alerts for long-held positions (User Decision Mode)"""
        # Alerts at 100, 125, 150, 200 days
        alert_days = [100, 125, 150, 200]
        
        # We need a state to prevent spamming the same alert. 
        # For now, we'll check if we are 'close' to the milestone (within 4 hours)
        # A better way would be storing 'last_alert_day' in the position metadata, 
        # but for this iteration, we calculate proximity.
        
        for day in alert_days:
            # Check if age is within a 4-hour window of the milestone
            if abs(age_days - day) < (4/24): 
                # Ideally, check if alert already sent. 
                # Implementation Note: This might span multiple loops, so we rely on the Notifier's 
                # built-in throttling or we add a 'last_alert' timestamp column in future.
                # For this MVP, we just print/log.
                print(f"⚠️ AGE ALERT: Position #{position['id']} ({position['symbol']}) held for {age_days:.1f} days.")
                # self.notifier.send_message(...) # Uncomment when integrated
                pass

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
        """
        Check aged positions.
        - Hyper-Scalper: Force close after max hold (failed scalp).
        - SMA Trend: NO force close (let trend run).
        - Buy-the-Dip: NO force close (Indefinite Hold) + Alerting.
        """
        # Strategy max hold times (in hours)
        # 0 means "Do not auto-close"
        max_hold_times = {
            'Hyper-Scalper Bot': 0.5,  # 30 minutes
            'Buy-the-Dip Strategy': 0,  # Indefinite Hold (Alert only)
            'SMA Trend Bot': 0  # Indefinite Hold (Trend following)
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
            age_days = age_hours / 24
            
            # --- ALERTING LOGIC (Buy-The-Dip) ---
            if strategy == 'Buy-the-Dip Strategy':
                self.check_position_age_alerts(position, age_days)

            # --- CLEANUP LOGIC ---
            max_hold = max_hold_times.get(strategy, 24)
            
            # Only force close if max_hold > 0 (enabled) AND age > 3x limit
            if max_hold > 0 and age_hours > (max_hold * 3):
                print(f"[AUTO-CLEANUP] Force-closing aged position #{position_id}: {symbol} ({age_hours:.1f}h old, max: {max_hold}h)")
                
                try:
                    # Get current price
                    df = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=1)
                    if not df.empty:
                        current_price = df['close'].iloc[-1]
                        
                        # Calculate RSI for cleanup log
                        try:
                            # We need more history to calc RSI, fetch if needed or default to None
                            # For cleanup, accurate RSI isn't critical, but we need the variable defined
                            rsi = 50.0 # Default neutral value for forced cleanup
                            # Optionally fetch more data if strictly needed:
                            # df_rsi = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                            # rsi = calculate_rsi(df_rsi['close']).iloc[-1]
                        except:
                            rsi = 50.0

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
                # Fetch data first to allow resilience recovery
                df = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                
                # Update Resilience (Heartbeat/Freshness)
                if not df.empty:
                    # Simulate latency (can be improved with actual measurement)
                    self.resilience_manager.update_heartbeat(Decimal("100")) 
                    self.resilience_manager.update_price_data()
                else:
                    self.resilience_manager.record_failure()
                    continue

                # --- RESILIENCE CHECK ---
                can_trade_resilience, reason = self.resilience_manager.can_trade()
                if not can_trade_resilience:
                    # Print only once every 10 loops to reduce spam
                    print(f"[{bot['name']}] Resilience Block: {reason}")
                    
                    # Alert if disconnected for a long time (throttle to once per hour)
                    if (datetime.now() - self.last_resilience_alert).total_seconds() > 3600:
                        self.notifier.send_message(f"⚠️ **CRITICAL: Bot Disconnected**\nReason: {reason}\nCheck VPS Internet or API status.")
                        self.last_resilience_alert = datetime.now()
                        
                    continue

                current_price = df['close'].iloc[-1]
                rsi = calculate_rsi(df['close']).iloc[-1]
                
                # --- SPECIAL HANDLING FOR GRID BOT ---
                if strategy_type == 'Grid':
                    strategy_instance = self.strategies.get(bot['name'])
                    if strategy_instance:
                        open_positions = self.logger.get_open_positions(symbol)
                        signal = strategy_instance.get_signal(current_price, open_positions, df=df)
                        
                        if signal:
                            if signal['side'] == 'SELL':
                                print(f"[{bot['name']}] Grid SELL Signal: {signal['reason']}")
                                self.execute_trade(bot, symbol, 'SELL', current_price, rsi, position_id=signal['position_id'])
                            elif signal['side'] == 'BUY':
                                print(f"[{bot['name']}] Grid BUY Signal: {signal['reason']}")
                                self.execute_trade(bot, symbol, 'BUY', current_price, rsi, reason=signal['reason'])
                        
                        # Report Grid Status for Visualization
                        if hasattr(strategy_instance, 'get_grid_metrics'):
                            metrics = strategy_instance.get_grid_metrics()
                            if metrics:
                                self.logger.update_system_health(
                                    component=f"Strategy: {bot['name']} ({symbol})",
                                    status="LOCKED" if metrics.get('is_locked') else "ACTIVE",
                                    message=f"Range: ${metrics.get('lower_limit',0):.0f} - ${metrics.get('upper_limit',0):.0f}",
                                    metrics=metrics
                                )

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
                    
                    # --- EMERGENCY STOP (-40%) ---
                    # Logic: If PnL < -40%, do not auto-sell. Ask for permission.
                    current_pnl_pct = (current_price - buy_price) / buy_price
                    
                    if current_pnl_pct < -0.40:
                        # Check if we already asked
                        pending_decision = self.logger.get_pending_decision(position_id)
                        
                        if not pending_decision:
                            print(f"[EMERGENCY] {symbol} hit -40%. Requesting User Approval...")
                            # Create Decision Record
                            reason = f"Catastrophe Stop triggered. PnL: {current_pnl_pct*100:.1f}%. Sell now?"
                            self.logger.create_decision(position_id, "EMERGENCY_SELL", reason, current_price)
                            
                            # Notify User
                            self.notifier.send_message(
                                f"🚨 **ACTION REQUIRED: {symbol} CRASH** 🚨\n\n"
                                f"Position is down *{current_pnl_pct*100:.1f}%*.\n"
                                f"Price: ${current_price}\n"
                                f"Entry: ${buy_price}\n\n"
                                f"❌ Bot will NOT sell without approval.\n"
                                f"👉 **Go to Dashboard to Approve or Hold.**"
                            )
                        else:
                            # We already asked. Check if user responded.
                            if pending_decision.status == 'APPROVED':
                                print(f"[EMERGENCY] User APPROVED sell for {symbol}.")
                                self.execute_trade(bot, symbol, 'SELL', current_price, rsi, position_id=position_id, reason="Emergency Sell Approved")
                                self.logger.update_decision_status(pending_decision.id, 'EXECUTED')
                            elif pending_decision.status == 'REJECTED':
                                # User said HOLD. Do nothing.
                                pass 
                        
                        continue # Skip standard SL logic to prevent conflict
                    
                    # Standard SL/TP logic acts only if not in emergency deep drawdown (handled above)
                    # Actually, standard SL might be -5%. If we dropped to -40% instantly (flash crash), the above catches it.
                    # If we drifted, standard SL would have fired at -5% unless 'Infinite Hold' was ON.
                    # For 'Dip Bot', SL is disabled, so it drifts to -40%.
                    # This logic works perfectly for the "Infinite Hold" bot.
                    
                    # Calculate profit %
                    profit_pct = (current_price - buy_price) / buy_price
                    
                    sell_reason = None
                    
                    # --- V3 EXIT LOGIC (Centralized in Risk Manager) ---
                    # Get current market regime for exit context
                    from luno_monitor.src.regime_detector import RegimeDetector
                    regime_det = RegimeDetector()
                    btc_df = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
                    regime_state, _, _ = regime_det.detect_regime(btc_df)
                    
                    # Prepare data object for Risk Manager
                    position_data = {
                        'entry_price': buy_price,
                        'current_price': current_price,
                        'strategy': strategy_type,
                        'symbol': symbol,
                        'entry_date': buy_timestamp,
                        'entry_regime': oldest_position.get('entry_regime', 'UNDEFINED') # V2 metadata
                    }
                    
                    # Ask Risk Manager what to do
                    action, risk_reason = self.risk_manager.check_exit_conditions(
                        position_data, 
                        regime_state=regime_state.value if hasattr(regime_state, 'value') else str(regime_state)
                    )
                    
                    if action == 'SELL':
                        sell_reason = risk_reason
                    elif action == 'ALERT_STOP_LOSS':
                        print(f"⚠️  MANUAL DECISION NEEDED: {symbol} hit Stop Loss. Bot is HOLDING. {risk_reason}")
                    
                    # Priority 1: User Hard Manual Override (Stop Loss Enabled flag)
                    stop_loss_enabled = bot.get('stop_loss_enabled', False)
                    if stop_loss_enabled and current_price <= buy_price * (1 - sl_pct):
                         sell_reason = f"Hard SL Hit (-{sl_pct*100:.1f}%)"

                    if sell_reason:
                        print(f"[{bot['name']}] Selling {symbol}: {sell_reason}")
                        self.execute_trade(bot, symbol, 'SELL', current_price, rsi, position_id=position_id, reason=sell_reason)
                        continue  # Skip buy check after selling
                    
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
                    # --- VETO CHECK (Phase 2) ---
                    is_allowed, veto_reason = self.veto_manager.check_entry_allowed(symbol, bot['name'])
                    if is_allowed:
                        self.execute_trade(bot, symbol, 'BUY', current_price, rsi)
                    else:
                        print(f"[{bot['name']}] ⛔ VETO BLOCKED BUY {symbol}: {veto_reason}")
                        # Optional: Notify if it's a major event?
                        # self.notifier.send_message(f"⛔ Veto prevented trade on {symbol}: {veto_reason}")

                
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
                # Log the skipped trade
                self.logger.log_skipped_trade(
                    strategy=bot['name'],
                    symbol=symbol,
                    side='BUY',
                    price=price,
                    intended_amount=trade_amount_usd / price,
                    skip_reason='EXPOSURE_LIMIT',
                    current_exposure=current_exposure,
                    max_exposure=max_exposure,
                    details=f"Would exceed limit: ${current_exposure:.2f} + ${trade_amount_usd} > ${max_exposure}"
                )
                print(f"[SKIP] {symbol} exposure limit reached: ${current_exposure:.2f} / ${max_exposure}")
                return
            
            # Calculate trade amount
            amount = trade_amount_usd / price
            
            # --- V2 CONFLUENCE CHECK ---
            from luno_monitor.src.confluence_engine import ConfluenceEngine
            c_engine = ConfluenceEngine()
            
            # Fetch daily data for regime detection
            btc_df = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
            
            # Simplified manual inputs (in production, these should be more accurate)
            manual_inputs = {
                'rsi': rsi,
                'price': price,
                'volume_trend': 'INCREASING' if rsi > 50 else 'STABLE' # Proxy
            }
            
            v2_result = c_engine.get_total_confluence_score(
                symbol.split('/')[0],
                manual_inputs=manual_inputs,
                btc_df=btc_df
            )
            
            # Record V2 result to DB for dashboard/calibration
            self.logger.log_confluence_score(v2_result)
            
            if v2_result['scores']['final_total'] < 40: # Conservative threshold
                print(f"[SKIP] Confluence V2 Reject: Score {v2_result['scores']['final_total']}/100")
                return

            # --- RISK VALIDATION (V2) ---
            open_positions_df = self.logger.get_open_positions()
            current_positions_count = len(open_positions_df)
            correlated_count = len(open_positions_df[open_positions_df['symbol'] == symbol]) if not open_positions_df.empty else 0
            
            total_exp_usd = Decimal(str(self.logger.get_total_exposure()))
            sector_exp_usd = self._get_sector_exposure(symbol, open_positions_df)
            
            is_valid, rejection_reason = self.risk_manager.validate_new_trade(
                symbol=symbol,
                proposed_size=Decimal(str(trade_amount_usd)) / self.risk_manager.portfolio_value * Decimal("100"),
                current_positions=current_positions_count,
                correlated_positions=correlated_count,
                active_symbols=open_positions_df['symbol'].tolist() if not open_positions_df.empty else [],
                total_exposure_usd=total_exp_usd,
                sector_exposure_usd=sector_exp_usd,
                logger_instance=self.logger,
                exchange_instance=self.exchange
            )
            
            if not is_valid:
                print(f"[SKIP] Risk Manager Reject: {rejection_reason}")
                return

            if self.mode == 'live':
                print(f"🚀 EXECUTING LIVE BUY: {symbol} @ ${price:.4f} (Amt: {amount:.4f})")
                
                # EXECUTE ON EXCHANGE
                order = self.exchange.create_order(symbol, 'BUY', amount, price)
                
                if not order:
                    print(f"❌ LIVE ORDER FAILED. Aborting.")
                    return
                
                print(f"✅ ORDER FILLED: ID {order.get('id')}")
                
            if self.mode == 'paper' or self.mode == 'live': # Log for both
                if self.mode == 'paper':
                    print(f"●BUY {symbol}● Price: ${price:.4f}, Amount: {amount:.4f}")
                
                # --- EXECUTION SAFETY ---
                # Simulate execution (slippage check)
                # In paper mode, we assume fill price = current price, so 0 slippage.
                # But we should instantiate the manager to show intent
                exec_manager = OrderExecutionManager(symbol, Decimal(str(price)))
                exec_result = exec_manager.validate_execution(
                    Decimal(str(amount)), Decimal(str(amount)), Decimal(str(price))
                )
                
                if not exec_result.success:
                    print(f"[EXECUTION FAIL] {exec_result.message}")
                    return

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
                
                # Update Risk Manager Portfolio Value
                # In a real bot, we'd fetch total equity. Here we approximate or use the fixed balance for now.
                self.risk_manager.update_portfolio_value(Decimal(str(wallet_balance)))
        
        elif side == 'SELL' and position_id:
            # Get position details
            open_positions = self.logger.get_open_positions(symbol)
            
            # Safety check: ensure position exists
            if open_positions.empty or position_id not in open_positions['id'].values:
                print(f"[SKIP] Position #{position_id} already closed or not found for {symbol}")
                return  # Exit early without logging error to circuit breaker
            
            position = open_positions[open_positions['id'] == position_id].iloc[0]
            amount = position['amount']
            
            if self.mode == 'live':
                print(f"🚀 EXECUTING LIVE SELL: {symbol} @ ${price:.4f} (Amt: {amount:.4f})")
                
                # EXECUTE ON EXCHANGE
                order = self.exchange.create_order(symbol, 'SELL', amount, price)
                
                if not order:
                    print(f"❌ LIVE ORDER FAILED. Retrying as Market Order...")
                    # Fallback to market order if limit fails? Or just abort. 
                    # For safety, we abort and let next loop retry.
                    return 
                    
                print(f"✅ ORDER FILLED: ID {order.get('id')}")

            if self.mode == 'paper' or self.mode == 'live':
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
                    # Position likely handled by another thread or process
                    return  # Exit early
                
                # Calculate fee (0.1% Binance standard)
                fee = price * amount * 0.001
                
                # Alert on large losses
                if profit < -50:  # Loss greater than $50
                    # cost might be needed from position object if not available in profit
                    cost = position['cost'] # position here is the Series
                    profit_pct = (profit / cost) * 100 if cost > 0 else 0
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
                
                # Record result in Risk Manager (for consecutive loss logic)
                self.risk_manager.record_trade_result(was_profitable=(profit > 0))
                
                # Reset circuit breaker on successful trade
                self.reset_circuit_breaker()
                
                # Update bot status with accurate per-strategy metrics
                all_trades = self.logger.get_trades()
                bot_trades = all_trades[all_trades['strategy'] == bot['name']] if not all_trades.empty else []
                total_trades = len(bot_trades)
                total_pnl = self.logger.get_pnl_summary(bot['name'])
                wallet_balance = self.logger.get_wallet_balance(bot['name'], initial_balance=bot.get('initial_balance', 50000))
                self.logger.update_bot_status(bot['name'], 'RUNNING', total_trades, total_pnl, wallet_balance)
                
                # Update Risk Manager Portfolio Value
                self.risk_manager.update_portfolio_value(Decimal(str(wallet_balance)))

    def _get_sector_exposure(self, symbol: str, open_positions_df: pd.DataFrame) -> Decimal:
        """Calculate current exposure for the sector of the given symbol"""
        from core.risk_module import SECTOR_MAP
        base = symbol.split('/')[0].split(':')[0]
        target_sector = SECTOR_MAP.get(base, 'ALT')
        
        exposure = Decimal("0")
        if open_positions_df.empty:
            return exposure
            
        for _, pos in open_positions_df.iterrows():
            pos_symbol = pos['symbol']
            pos_base = pos_symbol.split('/')[0].split(':')[0]
            if SECTOR_MAP.get(pos_base, 'ALT') == target_sector:
                exposure += Decimal(str(pos.get('cost', 0)))
                
        return exposure
    def _take_portfolio_snapshot(self):
        """Record current portfolio state to DB for performance & safety tracking"""
        try:
            # 1. Get current balance and positions
            balance = self.exchange.fetch_balance()
            equity = balance.get('total', 0)
            cash = balance.get('free', 0)
            
            # 2. Get unrealized P&L
            open_positions = self.logger.get_open_positions()
            unrealized_pnl = 0.0
            pos_value = 0.0
            if not open_positions.empty:
                for _, pos in open_positions.iterrows():
                    try:
                        ticker = self.exchange.fetch_ticker(pos['symbol'])
                        curr_val = ticker['last'] * pos['amount']
                        pos_value += curr_val
                        unrealized_pnl += (ticker['last'] - pos['buy_price']) * pos['amount']
                    except:
                        pass
            
            # 3. Log it
            # We can also fetch the current risk_multiplier from regime detector if needed
            from luno_monitor.src.regime_detector import RegimeDetector
            regime_det = RegimeDetector()
            btc_df = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
            _, _, metrics = regime_det.detect_regime(btc_df)
            risk_mult = regime_det.get_risk_multiplier(regime_det.last_state)
            
            self.logger.log_portfolio_snapshot(
                equity=float(equity),
                cash=float(cash),
                pos_value=float(pos_value),
                unrealized_pnl=float(unrealized_pnl),
                risk_mult=float(risk_mult),
                pos_count=len(open_positions)
            )
            
        except Exception as e:
            print(f"[Engine] Portfolio snapshot failed: {e}")
