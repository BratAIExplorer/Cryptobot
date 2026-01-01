import requests

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage" if token else None
        self._last_sent = {} # Track throttling: {key: datetime}

    def can_send_throttled_msg(self, key, hours=12):
        """Check if enough time has passed to send another message for this key."""
        from datetime import datetime, timedelta
        now = datetime.now()
        if key not in self._last_sent:
            self._last_sent[key] = now
            return True
        
        if now - self._last_sent[key] > timedelta(hours=hours):
            self._last_sent[key] = now
            return True
        return False

    def send_message(self, message):
        """Send a message to the configured Telegram chat."""
        if not self.token or not self.chat_id:
            print(f"[Notifier] No token/chat_id configured. Message skipped: {message}")
            return False

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(self.base_url, json=payload, timeout=5)
            if response.status_code == 200:
                return True
            else:
                print(f"[Notifier] Error sending message: {response.text}")
                return False
        except Exception as e:
            print(f"[Notifier] Exception: {e}")
            return False

    def notify_trade(self, symbol, side, price, amount, reason=""):
        """Format and send a trade notification."""
        icon = "🟢" if side == "BUY" else "🔴"
        msg = f"{icon} *{side} {symbol}*\n" \
              f"Price: `${price:.4f}`\n" \
              f"Amount: `{amount:.4f}`\n" \
              f"Reason: _{reason}_"
        self.send_message(msg)
    
    # ==================== CRITICAL ALERTS ====================
    
    def alert_circuit_breaker(self, error_count, error_msg=None, bot_name=None, auto_recovery_minutes=30):
        """Alert when circuit breaker is triggered with detailed context."""
        ctx = f" (Bot: {bot_name})" if bot_name else ""
        msg = f"🔴 *CIRCUIT BREAKER TRIGGERED*{ctx}\n\n" \
              f"⚠️ Bot has been paused due to {error_count} consecutive errors.\n"
        
        if error_msg:
            msg += f"❌ *Last Error:* `{error_msg}`\n\n"
            
        msg += f"⏰ Auto-recovery in {auto_recovery_minutes} minutes.\n\n" \
               f"Check logs: `pm2 logs crypto_bot` or `journalctl -u crypto_bot_runner -f`"
        self.send_message(msg)
    
    def alert_max_drawdown(self, current_pct, max_pct, current_equity, peak_equity):
        """Alert when approaching or hitting max drawdown limit."""
        if current_pct >= max_pct:
            icon = "🚨"
            status = "MAX DRAWDOWN HIT - BOT PAUSED"
        else:
            icon = "⚠️"
            status = "DRAWDOWN WARNING"
        
        msg = f"{icon} *{status}*\n\n" \
              f"Current Drawdown: `{current_pct:.1f}%`\n" \
              f"Max Allowed: `{max_pct:.0f}%`\n" \
              f"Peak Equity: `${peak_equity:,.2f}`\n" \
              f"Current Equity: `${current_equity:,.2f}`\n\n" \
              f"Loss: `${peak_equity - current_equity:,.2f}`"
        self.send_message(msg)
    
    def alert_no_activity(self, hours, diagnosis=None):
        """Alert when bot hasn't traded for specified hours with root cause analysis."""
        diagnosis_text = diagnosis if diagnosis else self._diagnose_inactivity()

        msg = f"⚠️ *NO TRADING ACTIVITY ALERT*\n\n" \
              f"⏰ **Duration:** {hours} hours\n\n" \
              f"🔍 **ROOT CAUSE DIAGNOSIS:**\n{diagnosis_text}\n\n" \
              f"📊 Check dashboard: http://srv1010193:8501"
        self.send_message(msg)

    def _diagnose_inactivity(self):
        """Analyze why bot is inactive - check for crashes, errors, circuit breakers."""
        import os
        from datetime import datetime

        # 1. Check for crash loop in recent logs
        try:
            log_file = f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    # Read last 300 lines for analysis
                    lines = f.readlines()
                    recent_logs = lines[-300:] if len(lines) > 300 else lines

                # Count error patterns
                error_lines = [l for l in recent_logs if 'Error processing' in l or 'cannot access local variable' in l]

                if len(error_lines) > 20:
                    # Extract error type
                    sample = error_lines[0].strip()
                    if 'regime_state' in sample:
                        return (
                            f"🔴 **CRASH LOOP - regime_state Bug**\n"
                            f"   • {len(error_lines)} crashes detected\n"
                            f"   • Error: `regime_state variable not defined`\n"
                            f"   • **ACTION:** Deploy latest fix from GitHub\n"
                            f"   • `git pull && systemctl restart cryptobot`"
                        )
                    else:
                        error_snippet = sample[:80] + "..." if len(sample) > 80 else sample
                        return (
                            f"🔴 **CRASH LOOP DETECTED**\n"
                            f"   • {len(error_lines)} errors in logs\n"
                            f"   • Sample: `{error_snippet}`\n"
                            f"   • **ACTION:** Check logs and fix bug"
                        )

                # Check if bot is evaluating coins
                eval_lines = [l for l in recent_logs if 'Evaluating' in l or 'DIP DETECTED' in l or 'Golden Cross' in l]
                if len(eval_lines) == 0:
                    return (
                        f"⚠️ **BOT NOT EVALUATING COINS**\n"
                        f"   • No 'Evaluating' messages in logs\n"
                        f"   • Possible: All strategies paused or filtered\n"
                        f"   • **ACTION:** Check confluence thresholds"
                    )

        except Exception as e:
            pass

        # 2. Check circuit breaker status
        try:
            from core.logger import TradeLogger
            logger = TradeLogger()
            cb = logger.get_circuit_breaker_status()
            if cb and cb.get('is_paused'):
                return (
                    f"⛔ **CIRCUIT BREAKER ACTIVE**\n"
                    f"   • Triggered: {cb.get('reason', 'Unknown')}\n"
                    f"   • **ACTION:** Clear with SQL command:\n"
                    f"   • `DELETE FROM circuit_breaker;`"
                )
        except:
            pass

        # 3. If no obvious issue detected
        return (
            f"📊 **NO CRITICAL ISSUES DETECTED**\n"
            f"   • No crashes or circuit breakers\n"
            f"   • Possible: Low market opportunities\n"
            f"   • **ACTION:** Check confluence scores in logs"
        )
    
    def alert_service_restart(self):
        """Notify when bot service restarts."""
        msg = f"🔄 *BOT SERVICE RESTARTED*\n\n" \
              f"The trading bot has been restarted.\n" \
              f"All strategies are initializing...\n\n" \
              f"Status: ✅ Running"
        self.send_message(msg)
    
    def alert_large_loss(self, symbol, loss_amount, loss_pct):
        """Alert on significant single trade loss."""
        msg = f"💥 *LARGE LOSS ALERT*\n\n" \
              f"Symbol: `{symbol}`\n" \
              f"Loss: `${loss_amount:.2f}` ({loss_pct:.1f}%)\n\n" \
              f"Review trade details on dashboard."
        self.send_message(msg)
    
    def send_daily_summary(self, stats):
        """Send daily performance summary."""
        msg = f"📊 *DAILY SUMMARY*\n\n" \
              f"Date: `{stats['date']}`\n" \
              f"Total P&L: `${stats['total_pnl']:+.2f}`\n" \
              f"Trades: `{stats['total_trades']}`\n" \
              f"Win Rate: `{stats['win_rate']:.1f}%`\n\n" \
              f"Best Strategy: *{stats['best_strategy']}*\n" \
              f"P&L: `${stats['best_pnl']:+.2f}`"
        self.send_message(msg)
    
    def alert_profit_milestone(self, milestone, total_pnl):
        """Celebrate profit milestones."""
        msg = f"🎉 *PROFIT MILESTONE REACHED!*\n\n" \
              f"Total Realized P&L: `${total_pnl:,.2f}`\n" \
              f"Milestone: `${milestone:,.0f}` 🏆\n\n" \
              f"Keep up the great work!"
        self.send_message(msg)

    # ==================== INTELLIGENCE ALERTS (PHASE 2) ====================

    def notify_confluence_signal(self, symbol, score, details, timeframe):
        """Send Rich Confluence Alert"""
        msg = (
            f"🧠 *High Conviction Signal* 🧠\n\n"
            f"Symbol: *{symbol}*\n"
            f"Score: *{score}/100*\n"
            f"Timeframe: {timeframe}\n\n"
            f"🔍 *Details*:\n{details}"
        )
        self.send_message(msg)

    def notify_veto_trigger(self, symbol, reason, rule_type):
        """Send Veto Alert"""
        msg = (
            f"🛡️ *Trade Vetoed* 🛡️\n\n"
            f"Symbol: *{symbol}*\n"
            f"Rule: {rule_type}\n"
            f"Reason: {reason}"
        )
        self.send_message(msg)

    def notify_startup(self, mode, active_bots):
        """Send Startup Summary (Throttled to once per 4 hours to prevent spam)"""
        # Only send if not sent in last 4 hours (unless it's a manual force start)
        if not self.can_send_throttled_msg("bot_startup_alert", hours=4):
            print("🕒 [NOTIFIER] Startup notification throttled.")
            return

        bots_list = "\n".join([f"- {b['name']} ({b.get('total_count', len(b['symbols']))} symbols)" for b in active_bots])
        msg = (
            f"🚀 *Bot Started* 🚀\n\n"
            f"Mode: *{mode.upper()}*\n"
            f"Active Strategies:\n{bots_list}\n\n"
            f"✅ Systems Check: OK"
        )
        self.send_message(msg)

    def notify_performance_summary(self, stats_list):
        """Periodic performance report (e.g., every 4h)"""
        summary = "📊 *Performance Summary (4h)* 📊\n\n"
        for s in stats_list:
            pnl_icon = "📈" if s['pnl'] >= 0 else "📉"
            summary += f"*{s['name']}*\n" \
                       f"{pnl_icon} PnL: `${s['pnl']:,.2f}`\n" \
                       f"💼 Bal: `${s['balance']:,.2f}` | 🔄 Trades: {s['trades']}\n\n"
        
        summary += f"🕒 Next update in 4 hours.\n" \
                   f"🔗 Dashboard: http://srv1010193:8501"
        self.send_message(summary)

    # ==================== PILLAR C: NEW COIN WATCHLIST ====================

    def notify_new_listing_detected(self, symbol, coin_info):
        """Alert when new coin is detected and classified"""
        type_emoji = {'A': '🆕', 'B': '🌱', 'C': '⭐'}
        risk_emoji = {'EXTREME': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
        
        coin_type = coin_info.get('type', 'A')
        classification = coin_info.get('classification', 'UNKNOWN')
        risk = coin_info.get('risk_level', 'UNKNOWN')
        age_days = coin_info.get('age_days', 'Unknown')
        waiting_period = coin_info.get('waiting_period_days', 30)
        
        msg = (
            f"{type_emoji.get(coin_type, '🔭')} *NEW LISTING DETECTED*\n\n"
            f"Symbol: *{symbol}*\n"
            f"Type: {coin_type} ({classification})\n"
            f"Age: {age_days} days old\n"
            f"Risk: {risk_emoji.get(risk, '⚪')} {risk}\n\n"
            f"⏳ Waiting Period: {waiting_period} days\n"
            f"📊 Status: WATCHLIST - No action required\n\n"
            f"This coin will be monitored automatically."
        )
        self.send_message(msg)
    
    def notify_watchlist_rejection(self, symbol, reason):
        """Alert when coin is auto-rejected"""
        msg = (
            f"❌ *AUTO-REJECTED*\n\n"
            f"Symbol: {symbol}\n"
            f"Reason: {reason}\n\n"
            f"This coin failed automatic filters and has been removed from the watchlist."
        )
        self.send_message(msg)
    
    def notify_manual_review_required(self, symbol, coin_type, performance_summary):
        """Alert when coin reaches manual review stage with deep-dive links"""
        base_symbol = symbol.split('/')[0]
        
        # Construct research links
        mexc_link = f"https://www.mexc.com/exchange/{base_symbol}_USDT"
        dextools_link = f"https://www.dextools.io/app/en/search?q={base_symbol}"
        coingecko_search = f"https://www.coingecko.com/en/search_queries?search={base_symbol}"
        
        msg = (
            f"📋 *MANUAL REVIEW REQUIRED*\n"
            f"Symbol: *{symbol}* (Type {coin_type})\n\n"
            f"*30-Day Performance:*\n"
            f"{performance_summary}\n\n"
            f"🔍 *Deep Dive Research:*\n"
            f"• [MEXC Chart]({mexc_link})\n"
            f"• [DEXTools Audit/LP]({dextools_link})\n"
            f"• [CoinGecko Info]({coingecko_search})\n\n"
            f"Action: Review on dashboard or reply with:\n"
            f"• `/graduate {symbol}` - Ready for activation\n"
            f"• `/reject {symbol}` - Delete from list"
        )
        self.send_message(msg)
    
    def notify_coin_graduated(self, symbol, coin_type, position_size):
        """Alert when coin graduates to Pillar B"""
        type_desc = {'A': 'Brand New', 'B': 'Emerging', 'C': 'Established'}

        msg = (
            f"🎓 *COIN GRADUATED*\n\n"
            f"Symbol: *{symbol}*\n"
            f"Type: {type_desc.get(coin_type, coin_type)}\n"
            f"Position Size: {position_size}%\n\n"
            f"✅ Added to Pillar B (Buy-the-Dip) watchlist\n"
            f"📊 Now eligible for automated trading"
        )
        self.send_message(msg)

    # ==================== ENHANCED TRADE ALERTS ====================

    def alert_stop_loss_hit(self, symbol, strategy, entry_price, exit_price, loss_amount, loss_pct):
        """Alert when stop loss is triggered"""
        msg = (
            f"🛑 *STOP LOSS HIT*\n\n"
            f"Symbol: *{symbol}*\n"
            f"Strategy: _{strategy}_\n\n"
            f"Entry: `${entry_price:.4f}`\n"
            f"Exit: `${exit_price:.4f}`\n"
            f"Loss: `${loss_amount:.2f}` ({loss_pct:.2f}%)\n\n"
            f"✅ Position closed - Capital preserved"
        )
        self.send_message(msg)

    def alert_take_profit_hit(self, symbol, strategy, entry_price, exit_price, profit_amount, profit_pct):
        """Alert when take profit target is reached"""
        msg = (
            f"🎯 *TAKE PROFIT HIT*\n\n"
            f"Symbol: *{symbol}*\n"
            f"Strategy: _{strategy}_\n\n"
            f"Entry: `${entry_price:.4f}`\n"
            f"Exit: `${exit_price:.4f}`\n"
            f"Profit: `${profit_amount:.2f}` (+{profit_pct:.2f}%)\n\n"
            f"🎉 Winner! Target reached"
        )
        self.send_message(msg)

    def alert_trailing_stop_hit(self, symbol, strategy, entry_price, exit_price, profit_amount, profit_pct, peak_profit_pct):
        """Alert when trailing stop is triggered"""
        msg = (
            f"📉 *TRAILING STOP HIT*\n\n"
            f"Symbol: *{symbol}*\n"
            f"Strategy: _{strategy}_\n\n"
            f"Entry: `${entry_price:.4f}`\n"
            f"Peak Profit: `+{peak_profit_pct:.2f}%`\n"
            f"Exit: `${exit_price:.4f}`\n"
            f"Final Profit: `${profit_amount:.2f}` (+{profit_pct:.2f}%)\n\n"
            f"✅ Profits secured via trailing stop"
        )
        self.send_message(msg)

    def alert_error(self, error_type, error_message, component="Bot"):
        """Alert on critical errors"""
        msg = (
            f"❌ *ERROR ALERT*\n\n"
            f"Component: {component}\n"
            f"Type: `{error_type}`\n"
            f"Message: `{error_message}`\n\n"
            f"Check logs immediately: `pm2 logs crypto_bot`"
        )
        self.send_message(msg)
