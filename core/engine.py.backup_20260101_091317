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
from .fundamental_analyzer import FundamentalAnalyzer
from .regime_detector import RegimeDetector, RegimeState
from .new_coin_detector import NewCoinDetector
from .coin_classifier import CoinClassifier
from .watchlist_tracker import WatchlistTracker
from .correlation_manager import CorrelationManager


class TradingEngine:
    def __init__(self, mode='paper', telegram_config=None, exchange='MEXC', db_path=None, 
                 risk_manager=None, resilience_manager=None, regime_detector=None, 
                 veto_manager=None, fundamental_analyzer=None):
        self.mode = mode
        self.exchange_name = exchange
        self.luno_exchange = None # Cache for Pillar A monitor
        
        # Use unified exchange for all trades
        from .exchange_unified import UnifiedExchange
        self.exchange = UnifiedExchange(exchange_name=exchange, mode=mode)
        
        # Initialize logger with db_path if provided, otherwise use default
        if db_path:
            self.logger = TradeLogger(db_path=db_path)
        else:
            self.logger = TradeLogger()
        
        # Initialize Safety Managers
        self.risk_manager = risk_manager or setup_safe_trading_bot('moderate')
        self.resilience_manager = resilience_manager or ExchangeResilienceManager("MEXC") 
        self.execution_manager = None # Initialized per trade
        self.regime_detector = regime_detector or RegimeDetector(db_path)
        self.veto_manager = veto_manager or VetoManager(self.exchange, self.logger)
        self.fundamental_analyzer = fundamental_analyzer or FundamentalAnalyzer(self.exchange, self.logger)
        
        # Initialize Notifier first as other components depend on it
        self.notifier = TelegramNotifier(
            token=telegram_config.get('token') if telegram_config else None,
            chat_id=telegram_config.get('chat_id') if telegram_config else None
        )
        
        # Pillar C: Hybrid Watchlist Components
        self.new_coin_detector = NewCoinDetector(self.exchange, self.logger)
        self.coin_classifier = CoinClassifier(self.logger)
        self.watchlist_tracker = WatchlistTracker(self.exchange, self.logger, self.notifier)
        self.last_watchlist_scan = None
        self.last_performance_pulse = None # For daily tracker run
        self.known_symbols_path = os.path.join(root_dir, 'data', 'known_symbols_mexc.json')

        # Hybrid v2.0: Correlation Manager (prevents over-concentration in correlated assets)
        self.correlation_manager = CorrelationManager(
            correlation_window=30,  # 30-day rolling correlation
            correlation_threshold=0.7  # 0.7+ considered highly correlated
        )
        self.correlation_matrix_last_update = None

        # Initialize Observability (Pass risk manager)
        self.system_monitor = SystemMonitor(self.logger, self.risk_manager, self.resilience_manager)
        
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
            # Send alert only when it FIRST opens
            if not was_open:
                # Update all bots to PAUSED in DB so Dashboard reflects reality
                for bot in self.active_bots:
                    self.logger.update_bot_status(bot['name'], 'PAUSED (Circuit Breaker)')
                
                # Send detailed alert
                self.notifier.alert_circuit_breaker(
                    error_count=status['consecutive_errors'],
                    error_msg=status.get('last_error_message')
                )
                print(f"🔴 CIRCUIT BREAKER TRIGGERED: {status['consecutive_errors']} errors.")
            
            # Print status to console (less noisy)
            if datetime.now().second % 60 == 0: # Print once a minute
                 print(f"🔴 CIRCUIT BREAKER OPEN - Bot is paused. Last Error: {status.get('last_error_message')}")
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
        # Warm up Regime Detector
        print("🌡️ Warming up Market Regime Detector...")
        try:
            start_ping = time.time()
            btc_df_macro = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
            latency = Decimal(str(int((time.time() - start_ping) * 1000)))
            
            if not btc_df_macro.empty:
                self.resilience_manager.update_heartbeat(latency)
                self.resilience_manager.update_price_data()
                state, conf, _ = self.regime_detector.detect_regime(btc_df_macro)
                print(f"✅ Market Regime Initialized: {state.value} (Confidence: {conf*100:.1f}%)")
            else:
                self.resilience_manager.record_failure()
                print("⚠️  Warning: Could not fetch BTC data for regime warm-up.")
        except Exception as e:
            self.resilience_manager.record_failure()
            print(f"❌ Regime Warm-up Failed: {e}")

        # Hybrid v2.0: Build correlation matrix for Buy-the-Dip strategy
        print("🔗 Building correlation matrix for portfolio diversification...")
        try:
            # Collect all symbols from all bots
            all_symbols = set()
            for bot in self.active_bots:
                symbols = bot.get('symbols', [bot.get('symbol')])
                all_symbols.update(symbols)

            # Build correlation matrix (30-day rolling)
            correlation_matrix = self.correlation_manager.build_correlation_matrix(
                list(all_symbols),
                lambda sym, **kwargs: self.exchange.fetch_ohlcv(sym, **kwargs)
            )

            self.correlation_matrix_last_update = datetime.now()
            print(f"✅ Correlation Matrix Built: {len(correlation_matrix)} pairs analyzed")
        except Exception as e:
            print(f"⚠️  Warning: Could not build correlation matrix: {e}")
            print("   (Correlation filtering will be disabled)")

        # Update bot status on start for ALL bots
        all_trades = self.logger.get_trades()
        for bot in self.active_bots:
            try:
                # Get actual trade count for this bot
                if not all_trades.empty:
                    bot_trades = all_trades[all_trades['strategy'] == bot['name']]
                    total_trades = len(bot_trades)
                else:
                    total_trades = 0
                    
                total_pnl = self.logger.get_pnl_summary(bot['name'])
                initial_bal = bot.get('initial_balance', 0.0)
                wallet_balance = self.logger.get_wallet_balance(bot['name'], initial_balance=initial_bal)
                
                print(f"[STARTUP] Updating {bot['name']}: Trades={total_trades}, PnL=${total_pnl}, Balance=${wallet_balance}")
                self.logger.update_bot_status(bot['name'], 'RUNNING', total_trades, total_pnl, wallet_balance)
            except Exception as e:
                print(f"❌ Error initializing status for bot {bot.get('name', 'Unknown')}: {e}")

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
            
        # --- GLOBAL MARKET REGIME VETO (Hard Veto) ---
        # Fetch 1d BTC data for macro trend
        start_ping = time.time()
        btc_df_macro = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
        latency = Decimal(str(int((time.time() - start_ping) * 1000)))
        
        if btc_df_macro is not None and not btc_df_macro.empty:
            self.resilience_manager.update_heartbeat(latency)
            self.resilience_manager.update_price_data()
            regime_state, _, _ = self.regime_detector.detect_regime(btc_df_macro)
            if not self.regime_detector.should_trade(regime_state):
                # Print only once every hour (or use throttled alert)
                if datetime.now().minute % 60 == 0:
                    print(f"🛑 GLOBAL VETO: Trading blocked due to {regime_state.value} regime.")
                return 
        else:
            self.resilience_manager.record_failure()
            # If we essential data is missing, we might still want to process exits, so don't return here
        
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
        
        # --- PILLAR A (LUNO) ALERTS ---
        self._check_luno_confluence_alerts()
        
        # --- MARKET MONITOR (New Listings) ---
        self._run_market_monitor()
        
        # --- WATCHLIST PERFORMANCE PULSE (Every 24h) ---
        now = datetime.utcnow()
        if not self.last_performance_pulse or (now - self.last_performance_pulse).total_seconds() >= 86400:
            print("💓 [WATCHLIST] Running daily performance pulse...")
            self.watchlist_tracker.update_watchlist_performance()
            self.last_performance_pulse = now

        # --- DISCOVERY SCAN (Every 4 hours or manually triggered) ---
        self._run_discovery_scan()

        # --- PERIODIC PERFORMANCE SUMMARY (Every 4h) ---
        if self.notifier and self.notifier.can_send_throttled_msg("periodic_performance_summary", hours=4):
            perf_stats = []
            for bot in self.active_bots:
                try:
                    pnl = self.logger.get_pnl_summary(bot['name'])
                    bal = self.logger.get_wallet_balance(bot['name'], initial_balance=bot.get('initial_balance', 0.0))
                    trades_df = self.logger.get_trades()
                    t_count = len(trades_df[trades_df['strategy'] == bot['name']]) if not trades_df.empty else 0
                    perf_stats.append({
                        'name': bot['name'],
                        'pnl': float(pnl),
                        'balance': float(bal),
                        'trades': t_count
                    })
                except:
                    continue
            if perf_stats:
                self.notifier.notify_performance_summary(perf_stats)

        for bot in self.active_bots:
            try:
                # --- Heartbeat & Status Update ---
                current_status = 'RUNNING'
                
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
                self.logger.update_bot_status(bot['name'], current_status, total_trades, total_pnl, wallet_balance)
                
                # 3. Process Strategy - Passing btc_df_macro to avoid redundant fetches
                self.process_bot(bot, btc_df_macro=btc_df_macro)
            except Exception as e:
                print(f"❌ Error in bot loop for {bot.get('name', 'Unknown')}: {e}")

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
                        profit = self.logger.close_position(position_id, current_price, expected_price=current_price, exit_rsi=rsi)
                        if profit is not None:
                            print(f"[AUTO-CLEANUP] Position #{position_id} closed with profit: ${profit:.2f}")
                            
                            # Log the trade with fee
                            amount = position['amount']
                            fee = current_price * amount * 0.001  # 0.1% fee
                            self.logger.log_trade(strategy, symbol, 'SELL', current_price, amount, 
                                                expected_price=current_price, fee=fee, rsi=rsi, position_id=position_id, engine_version='2.0')
                except Exception as e:
                    print(f"[AUTO-CLEANUP] Error closing aged position #{position_id}: {e}")


    def process_bot(self, bot, btc_df_macro=None):
        """Execute logic for a single bot configuration (can be multiple symbols)"""
        symbols = bot.get('symbols', [bot.get('symbol')])
        strategy_type = bot['type']
        
        # --- PILLAR C INTEGRATION: Add active watchlist coins to Buy-the-Dip ---
        watchlist_symbols_map = {} # To store manual allocation
        if bot['name'] == 'Buy-the-Dip Strategy':
            active_watchlist = self.logger.get_new_coin_watchlist()
            # Filter for active only (since get_new_coin_watchlist doesn't filter is_active in current implementation)
            if not active_watchlist.empty and 'is_active' in active_watchlist.columns:
                active_list = active_watchlist[active_watchlist['is_active'] == True]
                for _, w_coin in active_list.iterrows():
                    sym = w_coin['symbol']
                    if sym not in symbols:
                        symbols.append(sym)
                    watchlist_symbols_map[sym] = w_coin['manual_allocation_usd']
                    # Increase max exposure for this specific coin to match manual allocation
                    # so execute_trade doesn't reject it
                    bot['max_exposure_per_coin'] = max(bot.get('max_exposure_per_coin', 2000), w_coin['manual_allocation_usd'] * 2)

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

                # --- PER-COIN CRASH DETECTION ---
                is_crashing, crash_reason, crash_metrics = self.regime_detector.detect_coin_crash(
                    symbol, df, lookback_hours=24
                )

                if is_crashing:
                    # Log crash detection
                    print(f"⚠️  [{bot['name']}] CRASH DETECTED: {symbol} - {crash_reason}")

                    # Notify via Telegram (throttled to prevent spam)
                    alert_key = f"crash_{symbol}"
                    if self.notifier.can_send_throttled_msg(alert_key, hours=4):
                        self.notifier.send_message(
                            f"🚨 *COIN CRASH DETECTED*\n\n"
                            f"Symbol: *{symbol}*\n"
                            f"Reason: {crash_reason}\n"
                            f"Metrics: {crash_metrics.get('drawdown_24h_pct', 'N/A'):.1f}% drawdown\n\n"
                            f"⛔ Trading blocked for this coin for 4 hours"
                        )

                    # Skip this coin entirely - don't buy or sell during crash
                    continue

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
                                # Use manual override if this is a watchlist coin
                                bot_copy = bot.copy()
                                if symbol in watchlist_symbols_map:
                                    bot_copy['amount'] = watchlist_symbols_map[symbol]
                                    print(f"💰 [WATCHLIST] Using manual allocation: ${bot_copy['amount']} for {symbol}")
                                
                                self.execute_trade(bot_copy, symbol, 'BUY', current_price, rsi, reason=signal['reason'])
                        
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
                    # Use provided btc_df_macro or fetch if missing
                    if btc_df_macro is None or btc_df_macro.empty:
                        btc_df_macro = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
                    
                    regime_state, _, _ = self.regime_detector.detect_regime(btc_df_macro)
                    
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
                        # Add detailed logging for profit exits
                        if 'Take Profit' in str(risk_reason):
                            profit_pct = (current_price - buy_price) / buy_price * 100
                            print(f"💰 [PROFIT EXIT] {bot['name']} | {symbol}")
                            print(f"   Entry: ${buy_price:.6f} | Exit: ${current_price:.6f}")
                            print(f"   Profit: +{profit_pct:.2f}%")
                            print(f"   Reason: {risk_reason}")

                    elif action == 'ALERT_STOP_LOSS':
                        print(f"⚠️  MANUAL DECISION NEEDED: {symbol} hit Stop Loss. Bot is HOLDING. {risk_reason}")

                    elif action == 'ALERT_CHECKPOINT':
                        # Handle Buy-the-Dip checkpoint alerts
                        print(f"📅 [CHECKPOINT] {bot['name']} | {symbol}")
                        print(f"   {risk_reason}")

                        # Send Telegram notification
                        if self.notifier:
                            try:
                                self.notifier.send_message(
                                    f"📅 **Position Checkpoint Alert**\n\n"
                                    f"**Strategy:** {bot['name']}\n"
                                    f"**Symbol:** {symbol}\n\n"
                                    f"{risk_reason}\n\n"
                                    f"👉 Review position in dashboard if needed.\n"
                                    f"💡 Bot will continue holding until +5% profit target."
                                )
                            except Exception as e:
                                print(f"   (Telegram notification failed: {e})")

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
                    # SMA TREND V2: Crossover Detection + ADX Filter
                    sma_fast_period = bot.get('sma_fast', 20)
                    sma_slow_period = bot.get('sma_slow', 50)

                    # Calculate SMAs
                    sma_fast = calculate_sma(df['close'], period=sma_fast_period)
                    sma_slow = calculate_sma(df['close'], period=sma_slow_period)

                    # Get current and previous values for crossover detection
                    prev_sma_fast = sma_fast.iloc[-2]
                    prev_sma_slow = sma_slow.iloc[-2]
                    curr_sma_fast = sma_fast.iloc[-1]
                    curr_sma_slow = sma_slow.iloc[-1]

                    # Check for Golden Cross (Fast crosses ABOVE Slow)
                    use_crossover = bot.get('use_crossover', True)

                    if use_crossover:
                        # TRUE CROSSOVER: Only buy when SMA fast crosses above SMA slow
                        is_crossover = (prev_sma_fast <= prev_sma_slow and
                                       curr_sma_fast > curr_sma_slow)
                    else:
                        # LEGACY: Just check if SMA fast > SMA slow
                        is_crossover = (curr_sma_fast > curr_sma_slow)

                    if is_crossover:
                        # Additional filter: Price must be above both SMAs (strength confirmation)
                        price_above_smas = (current_price > curr_sma_fast and
                                          current_price > curr_sma_slow)

                        if price_above_smas:
                            # ADX Filter: Only trade strong trends
                            adx_threshold = bot.get('adx_threshold', 0)  # 0 = disabled

                            if adx_threshold > 0:
                                from utils.indicators import calculate_adx
                                adx = calculate_adx(df, period=14).iloc[-1]

                                if adx >= adx_threshold:
                                    signal = 'BUY'
                                    print(f"[{bot['name']}] {symbol} Golden Cross + ADX {adx:.1f} > {adx_threshold}")
                                else:
                                    # ADX too low - weak trend
                                    print(f"[{bot['name']}] {symbol} Golden Cross but ADX {adx:.1f} < {adx_threshold} (skip)")
                            else:
                                # No ADX filter
                                signal = 'BUY'
                                print(f"[{bot['name']}] {symbol} Golden Cross detected")

                elif strategy_type == 'Grid':
                    # Simple Grid/Mean Reversion: Buy if price is 3% below SMA 50
                    sma_50 = calculate_sma(df['close'], period=50).iloc[-1]
                    if current_price < sma_50 * 0.97:
                        signal = 'BUY'
                
                elif strategy_type == 'Buy-the-Dip':
                    # HYBRID V2.0: Regime-Aware Entry Filtering
                    # Check market regime before buying dips

                    # Get current regime state
                    regime_state_value = regime_state.value if hasattr(regime_state, 'value') else str(regime_state)

                    # Define top-tier coins for safer buying in bearish conditions
                    TOP_10_SAFE = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'MATIC']
                    coin_base = symbol.split('/')[0] if '/' in symbol else symbol
                    is_safe_coin = coin_base in TOP_10_SAFE

                    # REGIME FILTER: Apply different rules based on market conditions
                    skip_buy = False
                    skip_reason = None

                    if regime_state_value == 'CRISIS':
                        # CRISIS: Pause ALL buys (capital preservation)
                        skip_buy = True
                        skip_reason = f"⛔ CRISIS Regime: Pausing all buys to preserve capital"

                    elif regime_state_value in ['BEAR_CONFIRMED', 'TRANSITION_BEARISH']:
                        # BEAR: Only buy top 10 safest coins
                        if not is_safe_coin:
                            skip_buy = True
                            skip_reason = f"⚠️  BEAR Regime: Only buying top 10 coins ({coin_base} not in safe list)"

                    # If regime blocks this buy, log and skip
                    if skip_buy:
                        print(f"[{bot['name']}] {symbol} {skip_reason}")
                        pass  # Skip to next symbol
                    else:
                        # Regime allows buying - proceed with dip detection
                        dip_threshold = bot.get('dip_threshold', 0.08)

                        # Logic: Current Price vs 24h High or SMA
                        high_24h = df['high'].max()
                        current_dip = (high_24h - current_price) / high_24h

                        if current_dip >= dip_threshold:
                            print(f"[{bot['name']}] {symbol} DIP DETECTED: {current_dip*100:.1f}% | Regime: {regime_state_value}")

                            # Use manual override if this is a watchlist coin
                            bot_copy = bot.copy()
                            if symbol in watchlist_symbols_map:
                                bot_copy['amount'] = watchlist_symbols_map[symbol]
                                print(f"💰 [WATCHLIST] Using manual allocation: ${bot_copy['amount']} for {symbol}")

                            self.execute_trade(bot_copy, symbol, 'BUY', current_price, rsi, reason="BUY_THE_DIP", btc_df_macro=btc_df_macro)
                        else:
                            # If no dip, no signal
                            pass
                elif strategy_type == 'DIP': # Keep DIP strategy for now, if it's distinct
                    # Buy on 8-15% dips from 24h high
                    recent_high = df['high'].rolling(window=24).max().iloc[-1]
                    drop_pct = ((current_price - recent_high) / recent_high)
                    
                    # Use bot-specific dip threshold if provided, else default to 8%
                    dip_threshold = bot.get('dip_percentage', 0.08)
                    if drop_pct <= -dip_threshold and drop_pct >= -0.15:
                        signal = 'BUY'

                # Execute BUY
                if signal == 'BUY':
                    # --- VETO CHECK (Phase 2) ---
                    is_allowed, veto_reason = self.veto_manager.check_entry_allowed(symbol, bot['name'])
                    if not is_allowed:
                        print(f"[{bot['name']}] ⛔ VETO BLOCKED BUY {symbol}: {veto_reason}")
                        # Notify veto events via Telegram
                        if self.notifier:
                            self.notifier.notify_veto_trigger(symbol, veto_reason, "Market/News Veto")
                    else:
                        # --- PER-COIN NEWS CHECK ---
                        coin_news_veto, news_reason = self.veto_manager.check_coin_news(symbol)
                        if coin_news_veto:
                            print(f"[{bot['name']}] 📰 NEWS VETO: {symbol} - {news_reason}")
                            if self.notifier:
                                self.notifier.notify_veto_trigger(symbol, news_reason, "Negative News")
                        else:
                            # --- HYBRID V2.0: CORRELATION CHECK (for Buy-the-Dip only) ---
                            correlation_blocked = False
                            if strategy_type == 'Buy-the-Dip':
                                try:
                                    # Get all open positions for this strategy
                                    all_open_positions_df = self.logger.get_all_open_positions()
                                    if not all_open_positions_df.empty:
                                        # Filter for Buy-the-Dip positions only
                                        strategy_positions = all_open_positions_df[
                                            all_open_positions_df['strategy'] == bot['name']
                                        ]

                                        # Convert to list of dicts
                                        open_positions_list = strategy_positions.to_dict('records')

                                        # Check correlation risk (max 2 correlated positions allowed)
                                        should_block, corr_reason = self.correlation_manager.should_block_entry(
                                            symbol,
                                            open_positions_list,
                                            max_correlated_positions=2
                                        )

                                        if should_block:
                                            print(f"[{bot['name']}] {corr_reason}")
                                            correlation_blocked = True
                                except Exception as e:
                                    print(f"⚠️  Correlation check failed: {e} (allowing trade)")

                            # Execute trade if all checks pass
                            if not correlation_blocked:
                                self.execute_trade(bot, symbol, 'BUY', current_price, rsi, btc_df_macro=btc_df_macro)

                
            except Exception as e:
                print(f"Error processing {symbol} in {bot['name']}: {e}")
                # Increment error count and store the error message
                self.logger.increment_circuit_breaker_errors(message=f"[{bot['name']}] {symbol}: {str(e)}")
                # Notification is handled by check_circuit_breaker() to prevent spam

    def execute_trade(self, bot, symbol, side, price, rsi, position_id=None, reason=None, btc_df_macro=None):
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
            
            # Base amount for dynamic scaling
            base_amount = trade_amount_usd
            
            # --- V2 CONFLUENCE CHECK ---
            from confluence_engine import ConfluenceEngine
            c_engine = ConfluenceEngine(db_path=self.logger.db_path)
            
            # Use provided btc_df_macro or fetch if missing
            if btc_df_macro is None or btc_df_macro.empty:
                btc_df_macro = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
            
            # Simplified manual inputs (in production, these should be more accurate)
            manual_inputs = {
                'rsi': rsi,
                'price': price,
                'volume_trend': 'INCREASING' if rsi > 50 else 'STABLE' # Proxy
            }
            
            v2_result = c_engine.get_total_confluence_score(
                symbol.split('/')[0],
                manual_inputs=manual_inputs,
                btc_df=btc_df_macro
            )
            
            # Record V2 result to DB for dashboard/calibration
            if 'exchange' not in v2_result:
                v2_result['exchange'] = self.exchange_name
            self.logger.log_confluence_score(v2_result)
            
            # --- DYNAMIC TRANCHING ---
            v2_score = v2_result['scores']['final_total']
            
            if v2_score >= 85:
                # STRONG BUY: 40% of planned tranche
                trade_amount_usd = base_amount * 0.40
                print(f"🔥 HIGH CONVICTION: Score {v2_score}. Scaling to 40% (${trade_amount_usd:.2f})")
            elif v2_score >= 75:
                # MODERATE BUY: 25% of planned tranche
                trade_amount_usd = base_amount * 0.25
                print(f"✅ MODERATE CONVICTION: Score {v2_score}. Scaling to 25% (${trade_amount_usd:.2f})")
            else:
                # Score < 75: AVOID/WAIT
                print(f"[SKIP] Confluence V2 Reject: Score {v2_score}/100 (Threshold 75)")
                return

            # Recalculate amount with scaled trade_amount_usd
            amount = trade_amount_usd / price

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
                
                # Update position and log trade
                if side == 'BUY':
                    pos_id = self.logger.open_position(symbol, bot['name'], price, amount, expected_price=price, entry_rsi=rsi, exchange=self.exchange_name)
                    self.logger.log_trade(bot['name'], symbol, 'BUY', price, amount, expected_price=price, rsi=rsi, position_id=pos_id, exchange=self.exchange_name)
                
                if not exec_result.success:
                    print(f"[EXECUTION FAIL] {exec_result.message}")
                    return

                # Open position (FIFO) with entry RSI
                position_id = self.logger.open_position(symbol, bot['name'], price, amount, expected_price=price, entry_rsi=rsi)
                
                # Calculate fee (0.1% Binance standard)
                fee = price * amount * 0.001
                
                # Log trade (with versioning and fee)
                strategy_version = bot.get('version', '1.0')
                self.logger.log_trade(bot['name'], symbol, side, price, amount, expected_price=price, fee=fee, rsi=rsi, 
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
                profit = self.logger.close_position(position_id, price, expected_price=price, exit_rsi=rsi)
                
                # Safety check: Handle case where position wasn't found
                if profit is None:
                    # Position likely handled by another thread or process
                    return  # Exit early
                
                # Calculate fee (0.1% Binance standard)
                fee = price * amount * 0.001
                
                # Alert on large losses
                if profit is not None and profit < -50:  # Loss greater than $50
                    # cost might be needed from position object if not available in profit
                    cost = position['cost'] # position here is the Series
                    profit_pct = (profit / cost) * 100 if cost > 0 else 0
                    self.notifier.alert_large_loss(symbol, abs(profit), abs(profit_pct))
                
                # Update last trade time for no-activity monitoring
                self.last_trade_time = datetime.now()
                
                # Log trade (with versioning and fee)
                strategy_version = bot.get('version', '1.0')
                self.logger.log_trade(bot['name'], symbol, side, price, amount, expected_price=price, fee=fee, rsi=rsi, 
                                    position_id=position_id, engine_version='2.0', strategy_version=strategy_version)
                
                # Send Specific Notification based on exit reason
                buy_price = position['buy_price']
                profit_pct = (profit / position['cost']) * 100 if position['cost'] > 0 else 0

                # Determine notification type based on reason
                if reason and 'SL' in reason.upper():
                    # Stop Loss Hit
                    self.notifier.alert_stop_loss_hit(
                        symbol, bot['name'], buy_price, price,
                        abs(profit), abs(profit_pct)
                    )
                elif reason and 'Take Profit' in reason:
                    # Take Profit Hit
                    self.notifier.alert_take_profit_hit(
                        symbol, bot['name'], buy_price, price,
                        profit, profit_pct
                    )
                elif reason and 'Trailing' in reason:
                    # Trailing Stop Hit (extract peak if available)
                    peak_pct = position.get('peak_profit_pct', profit_pct)
                    self.notifier.alert_trailing_stop_hit(
                        symbol, bot['name'], buy_price, price,
                        profit, profit_pct, peak_pct
                    )
                else:
                    # Generic trade notification
                    profit_str = f"Profit: ${profit:.2f} ({profit_pct:+.2f}%)"
                    reason_str = f"{reason} - {profit_str}" if reason else profit_str
                    self.notifier.notify_trade(symbol, side, price, amount, reason=reason_str)
                
                # Record result in Risk Manager (for consecutive loss logic)
                self.risk_manager.record_trade_result(was_profitable=(profit is not None and profit > 0))
                
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
            from core.regime_detector import RegimeDetector
            regime_det = RegimeDetector()
            btc_df = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
            _, _, metrics = regime_det.detect_regime(btc_df)
            risk_mult = regime_det.get_risk_multiplier(regime_det.last_state)
            
            # Ensure we pass floats, extracting 'total' or 'free' if they are dicts (from CCXT)
            def extract_val(val, key='USDT'):
                if isinstance(val, dict): return val.get(key, 0.0)
                return float(val) if val is not None else 0.0

            self.logger.log_portfolio_snapshot(
                equity=extract_val(equity),
                cash=extract_val(cash),
                pos_value=float(pos_value),
                unrealized_pnl=float(unrealized_pnl),
                risk_mult=float(risk_mult),
                pos_count=len(open_positions)
            )
            
        except Exception as e:
            print(f"[Engine] Portfolio snapshot failed: {e}")

    def _check_luno_confluence_alerts(self):
        """Monitor Pillar A (Luno) assets for high-conviction buying opportunities"""
        import sys
        import os
        # Use relative paths from engine.py (which is in /core)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        luno_src = os.path.join(root_dir, 'luno-monitor', 'src')
        if luno_src not in sys.path: sys.path.append(luno_src)
        
        from confluence_engine import ConfluenceEngine
        from exchange_unified import UnifiedExchange
        
        # Reuse or Create Luno specifically for the confluence monitor
        if not self.luno_exchange:
            try:
                self.luno_exchange = UnifiedExchange(exchange_name='LUNO', mode=self.mode)
                print("🌑 [MONITOR] Using Luno API for Pillar A confluence...")
            except Exception as e:
                print(f"⚠️  [MONITOR] Luno API initialization failed: {e}. Falling back to {self.exchange_name}...")
                self.luno_exchange = self.exchange
            
        c_engine = ConfluenceEngine(db_path=self.logger.db_path, exchange_client=self.luno_exchange)
        major_assets = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT']
        
        # Fetch 1d BTC data for macro trend
        btc_df = self.luno_exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
        
        for symbol in major_assets:
            try:
                result = c_engine.get_automated_confluence_score(symbol, btc_df=btc_df)
                result['exchange'] = 'LUNO'
                score = result['scores']['final_total']
                
                # Record result to DB
                self.logger.log_confluence_score(result)
                
                # Alert Logic: Only high conviction (>75)
                if score >= 75:
                    rating = result['recommendation']['rating']
                    print(f"💎 PILLAR A ALERT: {symbol} score {score} ({rating})")
                    
                    # Throttle alerts (one per 12 hours per symbol)
                    alert_key = f"luno_alert_{symbol.split('/')[0]}"
                    if self.notifier.can_send_throttled_msg(alert_key, hours=12):
                        self.notifier.notify_confluence_signal(
                            symbol, 
                            score, 
                            f"Rating: {rating}\nRegime: {result['regime']['state']}",
                            "1h"
                        )
                        
            except Exception as e:
                print(f"[Luno Monitor] Alert check failed for {symbol}: {e}")

    def _run_discovery_scan(self):
        """Scan secondary watchlist for new opportunities (Discovery Mode)"""
        # Run every 4 hours based on clock
        now = datetime.now()
        if now.hour % 4 != 0 or now.minute > 5:
            return
            
        import sys
        import os
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        luno_monitor_path = os.path.join(root_dir, 'luno-monitor')
        luno_src = os.path.join(luno_monitor_path, 'src')
        if luno_monitor_path not in sys.path: sys.path.append(luno_monitor_path)
        if luno_src not in sys.path: sys.path.append(luno_src)
        
        from config_coins import DISCOVERY_WATCHLIST
        from confluence_engine import ConfluenceEngine
        from exchange_unified import UnifiedExchange
        
        # Discovery scan uses MEXC/Primary unless specified
        # (Usually MEXC has better liquidity/data for altcoins)
        c_engine = ConfluenceEngine(db_path=self.logger.db_path, exchange_client=self.exchange)
        
        print(f"🔍 [SCANNER] Starting discovery scan for {len(DISCOVERY_WATCHLIST)} assets using {self.exchange_name}...")
        
        # Fetch 1d BTC data for macro trend
        btc_df = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=250)
        
        found_opportunities = 0
        for symbol in DISCOVERY_WATCHLIST:
            try:
                result = c_engine.get_automated_confluence_score(symbol, btc_df=btc_df)
                result['exchange'] = self.exchange_name
                score = result['scores']['final_total']
                
                # Record result to DB
                self.logger.log_confluence_score(result)
                
                if score >= 75:
                    found_opportunities += 1
                    # Send alert for discovery coins (Throttle 24h)
                    if self.notifier.can_send_throttled_msg(f"discovery_{symbol}", hours=24):
                        self.notifier.notify_confluence_signal(
                            symbol,
                            score,
                            f"✨ DISCOVERY OPPORTUNITY ✨\nRating: {result['recommendation']['rating']}\nScore: {score}/100",
                            "1h"
                        )
                
                # Small sleep to respect rate limits
                time.sleep(1)
            except Exception as e:
                print(f"❌ Scanner failed for {symbol}: {e}")
        
        print(f"✅ [SCANNER] Scan complete. Found {found_opportunities} opportunities.")


    def _run_market_monitor(self):
        """
        Pillar C: Hybrid Watchlist - Phase 1
        Detect new MEXC listings, classify by age (Type A/B/C), alert only
        NO TRADING in Phase 1 - pure intelligence gathering
        """
        # Run every 30 minutes
        now = datetime.now()
        if self.last_watchlist_scan and (now - self.last_watchlist_scan).seconds < 1800:
            return
        
        self.last_watchlist_scan = now
        
        print(f"\n{'='*70}")
        print(f"🔭 [PILLAR C] Hybrid Watchlist - Scanning for new listings...")
        print(f"{'='*70}")
        
        try:
            # 1. Detect new listings
            new_symbols = self.new_coin_detector.detect_new_listings()
            
            if not new_symbols:
                print(f"[PILLAR C] No new listings detected this cycle")
                return
            
            # 2. Process each new listing
            from core.database import NewCoinWatchlist
            session = self.logger.db.get_session()
            
            for symbol in new_symbols:
                try:
                    # Check if already in database
                    existing = session.query(NewCoinWatchlist).filter_by(symbol=symbol).first()
                    if existing:
                        print(f"[PILLAR C] {symbol} already in watchlist, skipping")
                        continue
                    
                    # Classify coin by age
                    coin_info = self.coin_classifier.classify_coin(symbol)
                    
                    # Get listing metadata
                    metadata = self.new_coin_detector.get_listing_metadata(symbol)
                    
                    # Create database record
                    base_symbol = symbol.split('/')[0]
                    watchlist_entry = NewCoinWatchlist(
                        symbol=symbol,
                        base_symbol=base_symbol,
                        detected_at=datetime.utcnow(),
                        listing_date_mexc=datetime.utcnow(),  # Approximate
                        first_listing_date_anywhere=datetime.strptime(coin_info.get('first_listed', '2024-01-01'), '%Y-%m-%d') if coin_info.get('first_listed') else None,
                        coin_type=coin_info.get('type', 'A'),
                        coin_age_days=coin_info.get('age_days'),
                        classification=coin_info.get('classification', 'UNKNOWN'),
                        risk_level=coin_info.get('risk_level', 'EXTREME'),
                        status='MONITORING',
                        initial_price=metadata.get('price', 0),
                        initial_volume_24h=metadata.get('volume_24h', 0),
                        metadata_json=str(metadata)
                    )
                    
                    session.add(watchlist_entry)
                    session.commit()
                    
                    # Send Telegram alert
                    if self.notifier:
                        self.notifier.notify_new_listing_detected(symbol, coin_info)
                    
                    print(f"✅ [PILLAR C] Added {symbol} to watchlist (Type {coin_info.get('type')})")
                    
                except Exception as e:
                    print(f"❌ [PILLAR C] Error processing {symbol}: {e}")
                    session.rollback()
                    continue
            
            session.close()
            
            print(f"{'='*70}")
            print(f"✅ [PILLAR C] Scan complete. Processed {len(new_symbols)} new listings")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"❌ [PILLAR C] Market monitor failed: {e}")
