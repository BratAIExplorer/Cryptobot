#!/usr/bin/env python3
"""
🎯 INFINITE HOLD STRATEGY IMPLEMENTATION
User's Strategy: Hold forever until 5% profit, alerts at 60/90/120/200 days

CRITICAL: This script generates the exact code changes needed.
Do NOT run this script directly - it outputs code to be manually applied.
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    INFINITE HOLD STRATEGY - CODE CHANGES                      ║
║                                                                                ║
║  Strategy: Hold indefinitely until +5% profit                                 ║
║  Alerts: 60, 90, 120, 200 days (manual review)                               ║
║  Stop Loss: DISABLED (manual decision only)                                  ║
║  Catastrophic Floor: DISABLED (manual decision only)                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

""")

print("=" * 80)
print("CHANGE #1: Update core/risk_module.py")
print("=" * 80)
print("""
FILE: core/risk_module.py
FUNCTION: check_exit_conditions() (line 394)
ACTION: Replace entire function with this version:

def check_exit_conditions(self, position_data, regime_state: str = None) -> Tuple[str, Optional[str]]:
    \"""
    V4 Exit Engine - Buy-the-Dip Infinite Hold Strategy
    - Hold indefinitely until +5% profit
    - Alerts at 60, 90, 120, 200 days
    - NO auto-sell on losses (manual decision only)
    \"""
    current_price = Decimal(str(position_data['current_price']))
    entry_price = Decimal(str(position_data['entry_price']))
    strategy = position_data.get('strategy', 'Unknown')
    entry_date = position_data.get('entry_date')

    # Parse entry_date if string
    if isinstance(entry_date, str):
        try:
            entry_date = datetime.fromisoformat(entry_date)
        except:
            entry_date = datetime.utcnow()

    # 1. Calculate PnL
    pnl_pct = (current_price - entry_price) / entry_price

    # 2. Calculate position age
    hours_open = 0
    days_open = 0
    if entry_date:
        hours_open = (datetime.utcnow() - entry_date).total_seconds() / 3600
        days_open = hours_open / 24

    # ========================================
    # BUY-THE-DIP INFINITE HOLD STRATEGY
    # ========================================
    if strategy == "Buy-the-Dip Strategy":
        # RULE 1: Auto-sell ONLY at +5% profit (net 4.5% after fees)
        if pnl_pct >= Decimal("0.05"):
            return 'SELL', f"✅ Take Profit Reached (+{pnl_pct*100:.2f}%)"

        # RULE 2: Checkpoint Alerts (60, 90, 120, 200 days)
        checkpoint_days = [60, 90, 120, 200, 300, 365]
        for checkpoint in checkpoint_days:
            # Alert within 12 hours of checkpoint
            if abs(days_open - checkpoint) <= 0.5:
                return 'ALERT_CHECKPOINT', (
                    f"📅 Position Review: Day {days_open:.0f}\\n"
                    f"Current P&L: {pnl_pct*100:+.1f}%\\n"
                    f"Entry: ${entry_price:.6f} | Current: ${current_price:.6f}\\n"
                    f"Target: +5.0% (${entry_price * Decimal('1.05'):.6f})\\n"
                    f"💡 Review position but bot will continue holding until +5%"
                )

        # RULE 3: NO Stop Loss - Hold indefinitely
        # (User will manually intervene if needed via dashboard)

        # Default: HOLD and wait for profit
        return 'HOLD', None

    # ========================================
    # STANDARD LOGIC FOR OTHER STRATEGIES
    # (Grid Bot, SMA Trend, Hyper-Scalper, etc.)
    # ========================================

    # Regime-Aware Stop Loss
    sl_threshold = Decimal("-0.05")  # Default -5%
    if regime_state == 'CRISIS':
        sl_threshold = Decimal("-0.02")
    elif regime_state in ['BULL_CONFIRMED', 'TRANSITION_BULLISH']:
        sl_threshold = Decimal("-0.10")

    # Time-Based Stagnation (72 hours)
    if hours_open > 72 and pnl_pct < 0.01:
        return 'SELL', f"Stagnation: Open {hours_open:.1f}h with <1% profit"

    # Regime Switch Veto
    entry_regime = position_data.get('entry_regime')
    if entry_regime in ['BULL_CONFIRMED', 'TRANSITION_BULLISH'] and regime_state == 'CRISIS':
        if pnl_pct > -0.01:
            return 'SELL', f"Regime Veto: Market shifted to CRISIS"

    # Take Profit (strategy-specific)
    tp_target = Decimal("0.03")  # Default 3%
    if strategy == "Hyper-Scalper Bot":
        tp_target = Decimal("0.01")
    elif strategy == "Grid Bot BTC" or strategy == "Grid Bot ETH":
        tp_target = Decimal("0.015")
    elif strategy == "SMA Trend Bot":
        tp_target = Decimal("0.10")

    if pnl_pct >= tp_target:
         return 'SELL', f"Take Profit Reached (+{pnl_pct*100:.2f}%)"

    # Stop Loss (alert only for non-Dip strategies)
    if pnl_pct <= sl_threshold:
        return 'ALERT_STOP_LOSS', f"Stop Loss ({pnl_pct*100:.2f}%) [Regime: {regime_state}]"

    return 'HOLD', None
""")

print("\n" + "=" * 80)
print("CHANGE #2: Update core/engine.py")
print("=" * 80)
print("""
FILE: core/engine.py
LOCATION: Around line 670-673 (in process_bot function)
ACTION: Update action handling to include ALERT_CHECKPOINT

FIND THIS CODE:
    if action == 'SELL':
        sell_reason = risk_reason
    elif action == 'ALERT_STOP_LOSS':
        print(f"⚠️  MANUAL DECISION NEEDED: {symbol} hit Stop Loss. Bot is HOLDING. {risk_reason}")

REPLACE WITH:
    if action == 'SELL':
        sell_reason = risk_reason
        # Add detailed logging for profit exits
        if 'Take Profit' in str(risk_reason):
            print(f"💰 [PROFIT EXIT] {bot['name']} | {symbol}")
            print(f"   Entry: ${buy_price:.6f} | Exit: ${current_price:.6f}")
            print(f"   Profit: +{((current_price - buy_price) / buy_price * 100):.2f}%")
            print(f"   Reason: {risk_reason}")

    elif action == 'ALERT_STOP_LOSS':
        print(f"⚠️  MANUAL DECISION NEEDED: {symbol} hit Stop Loss. Bot is HOLDING. {risk_reason}")

    elif action == 'ALERT_CHECKPOINT':
        # NEW: Handle checkpoint alerts for Buy-the-Dip
        print(f"📅 [CHECKPOINT] {bot['name']} | {symbol}")
        print(f"   {risk_reason}")

        # Send Telegram notification
        if self.notifier and hasattr(self.notifier, 'send_message'):
            try:
                self.notifier.send_message(
                    f"📅 **Position Checkpoint Alert**\\n\\n"
                    f"**Strategy:** {bot['name']}\\n"
                    f"**Symbol:** {symbol}\\n\\n"
                    f"{risk_reason}\\n\\n"
                    f"👉 Review position in dashboard if needed.\\n"
                    f"💡 Bot will continue holding until +5% profit target is reached."
                )
            except Exception as e:
                print(f"   (Telegram notification failed: {e})")
""")

print("\n" + "=" * 80)
print("CHANGE #3: Update run_bot.py")
print("=" * 80)
print("""
FILE: run_bot.py
LOCATION: Lines 135-174 (Buy-the-Dip Strategy config)
ACTION: Update configuration to match new strategy

REPLACE THE ENTIRE Buy-the-Dip config block with:

    engine.add_bot({
        'name': 'Buy-the-Dip Strategy',
        'type': 'Buy-the-Dip',
        'symbols': [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT',
            'XRP/USDT', 'DOGE/USDT', 'ADA/USDT', 'TRX/USDT',
            'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'UNI/USDT'
        ],

        # Position Sizing
        'amount': 25,  # Start small, scale if successful
        'initial_balance': 3000,
        'max_exposure_per_coin': 200,

        # Entry Settings
        'dip_percentage': 0.05,       # 5% dip to trigger buy
        'min_confluence': 65,         # Confluence score threshold

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # EXIT STRATEGY: INFINITE HOLD
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        'take_profit_pct': 0.05,      # ✅ Auto-sell at +5% (net 4.5% after fees)
        'stop_loss_pct': None,        # ✅ DISABLED (never auto-sell at loss)
        'stop_loss_enabled': False,   # ✅ DISABLED
        'max_hold_hours': None,       # ✅ Hold indefinitely until profitable

        # Checkpoint Alerts (informational only)
        'checkpoint_days': [60, 90, 120, 200, 300, 365],

        # Trend Filters (Multi-timeframe validation)
        'sma_fast': 7,                # 7-day SMA
        'sma_slow': 21,               # 21-day SMA
        'require_above_both': True,   # Must be above both SMAs

        # Smart Conditional Cooldown
        'cooldown_after_profit': 6,   # 6 hours after profitable exit
        'cooldown_after_loss': 0,     # Not applicable (no losses sold)
        'cooldown_same_day': 12,      # 12h minimum between buys
        'max_positions_per_coin': 2,  # Can average down once

        # Safety Limits
        'max_daily_trades': 3,

        # Circuit Breaker (Emergency only - manual intervention)
        'circuit_breaker_daily': -500,    # Pause if -$500 daily loss
        'circuit_breaker_weekly': -1000   # Pause if -$1000 weekly loss
    })
""")

print("\n" + "=" * 80)
print("CHANGE #4: Add Enhanced Logging")
print("=" * 80)
print("""
FILE: core/logger.py
ACTION: Add method for exit tracking (optional but recommended)

Add this method to the TradeLogger class:

    def log_exit_attempt(self, strategy, symbol, action, reason, current_price, entry_price):
        \"""
        Log every exit check for debugging why positions don't close
        \"""
        pnl_pct = (current_price - entry_price) / entry_price * 100

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'strategy': strategy,
            'symbol': symbol,
            'action': action,  # SELL, HOLD, ALERT_CHECKPOINT, ALERT_STOP_LOSS
            'reason': reason,
            'entry_price': float(entry_price),
            'current_price': float(current_price),
            'pnl_pct': float(pnl_pct)
        }

        # Append to CSV log file
        import csv
        import os

        log_file = 'data/exit_checks.csv'
        file_exists = os.path.exists(log_file)

        with open(log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=log_entry.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(log_entry)

        # Also log SELL actions to console for visibility
        if action == 'SELL':
            print(f"📝 [EXIT LOG] {strategy} | {symbol} | {action} | {reason} | {pnl_pct:+.2f}%")


Then in core/engine.py, call this after checking exit conditions:

    # After line where action, risk_reason = self.risk_manager.check_exit_conditions(...)
    # Add:
    self.logger.log_exit_attempt(
        strategy=bot['name'],
        symbol=symbol,
        action=action,
        reason=risk_reason or 'HOLD',
        current_price=current_price,
        entry_price=buy_price
    )
""")

print("\n" + "=" * 80)
print("DEPLOYMENT CHECKLIST")
print("=" * 80)
print("""
[ ] 1. Backup current code:
      cd /Antigravity/antigravity/scratch/crypto_trading_bot
      git add -A
      git commit -m "backup: before infinite hold strategy"
      git push

[ ] 2. Apply code changes:
      - Update core/risk_module.py (Change #1)
      - Update core/engine.py (Change #2)
      - Update run_bot.py (Change #3)
      - Update core/logger.py (Change #4 - optional)

[ ] 3. Test configuration:
      python3 -c "from core.risk_module import RiskManager; print('✅ Import successful')"

[ ] 4. Stop current bot:
      touch STOP_SIGNAL

[ ] 5. Wait for clean shutdown:
      tail -f bot.log  # Watch for shutdown message

[ ] 6. Start with new strategy:
      python3 run_bot.py

[ ] 7. Monitor for 24 hours:
      - Watch for +5% profit hits
      - Verify NO auto-sells on losses
      - Check exit_checks.csv log file

[ ] 8. Verify logging:
      tail -f data/exit_checks.csv

[ ] 9. Test checkpoint alerts (simulate):
      # Manually update a position's entry_date to 60 days ago
      # Verify alert triggers

[ ] 10. Production deployment:
       # Once validated in paper mode, deploy to live
""")

print("\n" + "=" * 80)
print("EXPECTED BEHAVIOR EXAMPLES")
print("=" * 80)
print("""
Scenario 1: Position Reaches +5.0%
─────────────────────────────────────────
Symbol: SOL/USDT
Entry: $139.72
Current: $146.70 (+5.0%)

ACTION: ✅ AUTO-SELL
REASON: "✅ Take Profit Reached (+5.00%)"
NET PROFIT: +4.5% (after fees)
TELEGRAM: "💰 Profit exit: SOL/USDT +5.0%"


Scenario 2: Position at -15% After 30 Days
─────────────────────────────────────────
Symbol: XRP/USDT
Entry: $2.126
Current: $1.807 (-15.0%)
Days Held: 30

ACTION: ✅ HOLD
REASON: None (waiting for +5%)
ALERT: None (checkpoint at 60 days)


Scenario 3: Position at -20% After 60 Days
─────────────────────────────────────────
Symbol: DOT/USDT
Entry: $2.258
Current: $1.806 (-20.0%)
Days Held: 60

ACTION: ✅ HOLD (continue waiting)
REASON: None
ALERT: "📅 Position Review: Day 60
        Current P&L: -20.0%
        Target: +5.0% ($2.371)"
TELEGRAM: ✅ Checkpoint notification sent


Scenario 4: Position at -45% After 120 Days
─────────────────────────────────────────
Symbol: PEPE/USDT
Entry: $0.000005
Current: $0.00000275 (-45%)
Days Held: 120

ACTION: ✅ HOLD (no auto-sell)
REASON: None
ALERT: "📅 Position Review: Day 120
        Current P&L: -45.0%
        💡 Consider manual review"
USER DECISION: Hold longer OR manually sell via dashboard


Scenario 5: Recovery After Long Hold
─────────────────────────────────────
Symbol: ADA/USDT
Entry: $0.4283
Current: $0.4497 (+5.0%)
Days Held: 180

ACTION: ✅ AUTO-SELL (finally profitable!)
REASON: "✅ Take Profit Reached (+5.00%)"
NET PROFIT: +4.5% after 6 months
TELEGRAM: "💰 Long hold paid off: ADA/USDT +5% (180 days)"
""")

print("\n" + "=" * 80)
print("✅ IMPLEMENTATION GUIDE COMPLETE")
print("=" * 80)
print("""
Next steps:
1. Review all code changes above
2. Apply changes manually (copy/paste each section)
3. Test in paper mode
4. Deploy to production once validated

Need help with implementation? I can:
- Create automated patch files
- Generate test cases
- Build manual position review dashboard
""")
