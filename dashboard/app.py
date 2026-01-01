import streamlit as st
import pandas as pd
import time
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.logger import TradeLogger
from dashboard.components import plot_candle_chart, strategy_config_ui
from core.exchange import ExchangeInterface
from dashboard.beginner_helpers import (
    get_traffic_light, get_signal_assessment, get_signal_breakdown, translate_term,
    simplify_percentage, format_dollar_amount, get_regime_indicator
)
from intelligence.master_decision import MasterDecisionEngine

st.set_page_config(page_title="My Crypto Bot", layout="wide", page_icon="🤖", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, rgba(31,119,180,0.1) 0%, rgba(255,127,14,0.1) 100%);
        border-radius: 10px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
    }
    .bot-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .status-running {
        background: #10b981;
        color: white;
    }
    .status-stopped {
        background: #ef4444;
        color: white;
    }
    .help-box {
        background: #f0f9ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Header with gradient background
st.markdown('<h1 class="main-header">🤖 My Crypto Trading Bot</h1>', unsafe_allow_html=True)

# --- AUTHENTICATION ---
import hashlib
import plotly.graph_objects as go

def check_password():
    """Returns True if the user had a correct password."""
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    password = st.text_input("Password", type="password", key="login_password_input")
    
    if password:
        # Check against environment variable FIRST (if set)
        env_password = os.environ.get("DASHBOARD_PASSWORD")
        if env_password and password.strip() == env_password:
            st.session_state["password_correct"] = True
            st.rerun()
            return True
            
        # Check against hardcoded hash (admin123)
        input_hash = hashlib.sha256(password.strip().encode()).hexdigest()
        MASTER_HASH = "240be518fabd2724ddb6f04eeb1da596740641078f7d5c90380bcbf29ef65302"
        
        if input_hash == MASTER_HASH:
            st.session_state["password_correct"] = True
            st.rerun()
            return True
        else:
            st.error("😕 Password incorrect")
            st.write(f"Entry length: {len(password.strip())} characters")
            return False
            
    return False

# TEMPORARILY DISABLED FOR DEBUGGING
# if not check_password():
#     st.stop()

# --- ENVIRONMENT SELECTOR ---
st.sidebar.title("⚙️ Dashboard Settings")

# BEGINNER MODE TOGGLE (Default: ON)
if 'beginner_mode' not in st.session_state:
    st.session_state['beginner_mode'] = True

# More prominent beginner mode toggle
st.sidebar.markdown("### 🎓 Display Mode")
beginner_mode = st.sidebar.toggle(
    "Simple Language Mode",
    value=st.session_state['beginner_mode'],
    help="Turn this ON for plain English explanations (recommended for beginners). Turn OFF for technical trading terms."
)
st.session_state['beginner_mode'] = beginner_mode

if beginner_mode:
    st.sidebar.success("✅ **Simple Mode ON**")
    st.sidebar.caption("🗣️ Everything explained in plain English")
else:
    st.sidebar.info("📊 **Technical Mode ON**")
    st.sidebar.caption("📈 Showing advanced trading metrics")

st.sidebar.markdown("---")

# Trading Environment
st.sidebar.markdown("### 💼 Trading Environment")
env_mode = st.sidebar.radio(
    "Select Mode:",
    ["Paper Trading (Practice)", "LIVE TRADING (Real Money)"],
    index=0,
    help="Paper Trading = Practice mode with fake money. LIVE = Real money trading!"
)
mode_slug = 'live' if env_mode == "LIVE TRADING (Real Money)" else 'paper'

if env_mode == "LIVE TRADING (Real Money)":
    st.sidebar.warning("⚠️ **LIVE MODE**\nYou are viewing real money!")
else:
    st.sidebar.info("🎮 **PRACTICE MODE**\nNo real money at risk")

# Initialize Logger with selected mode (Resilient version)
try:
    logger = TradeLogger(mode=mode_slug)
except TypeError:
    # Fallback if VPS is using old cached version without 'mode' arg
    logger = TradeLogger()
    
exchange = ExchangeInterface(mode=mode_slug)

st.sidebar.markdown("---")

# --- RISK METER (Regime Detection) ---
st.sidebar.markdown("### 🌡️ Market Conditions")
try:
    regime_df = logger.get_recent_market_regimes(limit=1)
    if not regime_df.empty:
        latest = regime_df.iloc[0]
        state = latest['regime']
        risk_multiplier = latest['risk_multiplier']

        regime_colors = {
            'BULL_CONFIRMED': '#00FF00',
            'TRANSITION_BULLISH': '#90EE90',
            'UNDEFINED': '#FFFF00',
            'TRANSITION_BEARISH': '#FFA500',
            'BEAR_CONFIRMED': '#FF4500',
            'CRISIS': '#8B0000'
        }

        if beginner_mode:
            # Simple market mood display with better formatting
            emoji, description, explanation = get_regime_indicator(state)
            st.sidebar.markdown(f"#### {emoji} **{description}**")
            st.sidebar.info(f"{explanation}")

            # Add a simple visual indicator
            if state in ['BULL_CONFIRMED', 'TRANSITION_BULLISH']:
                st.sidebar.success("✅ Good time for trading")
            elif state == 'UNDEFINED':
                st.sidebar.warning("⚠️ Be careful - market unclear")
            else:
                st.sidebar.error("🛑 Bot will be very cautious")
        else:
            # Technical risk meter
            fig_risk = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = risk_multiplier * 100,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"Market Regime: {state}", 'font': {'size': 14}},
                gauge = {
                    'axis': {'range': [0, 125], 'tickwidth': 1},
                    'bar': {'color': regime_colors.get(state, "gray")},
                    'steps': [
                        {'range': [0, 25], 'color': "rgba(255, 69, 0, 0.3)"},
                        {'range': [25, 75], 'color': "rgba(255, 165, 0, 0.3)"},
                        {'range': [75, 125], 'color': "rgba(0, 255, 0, 0.3)"}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': risk_multiplier * 100
                    }
                }
            ))
            fig_risk.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10))
            st.sidebar.plotly_chart(fig_risk, use_container_width=True)
except Exception as e:
    if beginner_mode:
        st.sidebar.info("⏳ Checking market conditions...")
    else:
        st.sidebar.info("Regime monitoring inactive...")

# --- OBSERVABILITY SECTION ---
st.sidebar.subheader("🏥 System Health")
try:
    health_df = logger.get_system_health()
    if not health_df.empty:
        for _, row in health_df.iterrows():
            # Status Color Mapping
            status_map = {
                "HEALTHY": "🟢",
                "WARNING": "🟡",
                "BLOCKED": "🔴",
                "UNKNOWN": "⚪"
            }
            icon = status_map.get(row['status'], "⚪")
            
            with st.sidebar.expander(f"{icon} {row['component']}", expanded=(row['status'] != 'HEALTHY')):
                st.write(f"**Status:** {row['status']}")
                st.write(f"**Msg:** {row['message']}")
                st.caption(f"Updated: {row['last_updated']}")
                
                # Parse Metrics JSON
                try:
                    import json
                    metrics = json.loads(row['metrics_json'])
                    if metrics:
                        st.divider()
                        for k, v in metrics.items():
                            st.write(f"{k.replace('_', ' ').title()}: `{v}`")
                except:
                    pass
    else:
        st.sidebar.info("Waiting for health snapshot...")
except Exception as e:
    st.sidebar.error(f"Health Monitor Error: {e}")

# Kill Switch
st.sidebar.subheader("🚨 Emergency Control")
if st.sidebar.button("🛑 STOP BOT IMMEDIATElY"):
    with open("STOP_SIGNAL", "w") as f:
        f.write("STOP")
    st.sidebar.error("STOP SIGNAL SENT! Bot should exit shortly.")

# --- PENDING APPROVALS ---
# Query Pending Decisions directly for UI speed or add method to logger
try:
    # Quick dirty query using session from logger (or add method)
    # Adding method 'get_all_pending_decisions' in logger would be cleaner but for now manual query logic
    # Actually, let's just inspect active positions with decisions?
    # Better: Add 'get_active_decisions' to Logger. I'll rely on a direct session here for MVP speed.
    session = logger.db.get_session()
    from core.database import Decision, Position
    pending = session.query(Decision, Position).join(Position).filter(Decision.status == 'PENDING').all()
    session.close()
    
    if pending:
        st.sidebar.error(f"🚨 {len(pending)} PENDING DECISIONS")
        for decision, pos in pending:
            with st.sidebar.form(key=f"decision_{decision.id}"):
                st.write(f"**{pos.symbol}**")
                st.caption(decision.rationale)
                st.write(f"Current PnL: {pos.unrealized_pnl_pct*100:.1f}%")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ SELL"):
                        # Update DB
                        logger.update_decision_status(decision.id, 'APPROVED')
                        st.success("Approved!")
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ HOLD"):
                        logger.update_decision_status(decision.id, 'REJECTED')
                        st.info("Rejected. HODLing.")
                        st.rerun()
except Exception as e:
    pass # Don't crash UI on DB lock

st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Legal & Compliance")
if st.sidebar.button("📄 Generate Tax & Audit Reports"):
    with st.spinner("Generating CSV reports..."):
        tax_path, audit_path = logger.export_compliance_reports()
        
        if tax_path and os.path.exists(tax_path):
            with open(tax_path, "rb") as f:
                st.sidebar.download_button(
                    label="📥 Download Tax Report",
                    data=f,
                    file_name=os.path.basename(tax_path),
                    mime="text/csv"
                )
        
        if audit_path and os.path.exists(audit_path):
            with open(audit_path, "rb") as f:
                st.sidebar.download_button(
                    label="📥 Download Audit Log",
                    data=f,
                    file_name=os.path.basename(audit_path),
                    mime="text/csv"
                )
        
        if tax_path and audit_path:
            st.sidebar.success("Reports generated!")

st.sidebar.markdown("---")
st.sidebar.info("The bot is running as a separate service. Use this dashboard to monitor performance.")

# ===========================================
# SUMMARY DASHBOARD AT THE TOP
# ===========================================
st.markdown("### 📊 Quick Overview")

# Get summary metrics
all_bot_status = logger.get_bot_status()
open_positions = logger.get_open_positions()
trades = logger.get_trades()

# Calculate totals
total_bots = len(all_bot_status) if all_bot_status is not None and not all_bot_status.empty else 0
running_bots = len(all_bot_status[all_bot_status['status'] == 'RUNNING']) if all_bot_status is not None and not all_bot_status.empty else 0
total_wallet = all_bot_status['wallet_balance'].sum() if all_bot_status is not None and not all_bot_status.empty else 0
total_pnl = all_bot_status['total_pnl'].sum() if all_bot_status is not None and not all_bot_status.empty else 0
total_positions = len(open_positions) if not open_positions.empty else 0
total_trades_count = len(trades) if not trades.empty else 0

# Display summary metrics in colorful cards
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="🤖 Active Bots" if beginner_mode else "Active Bots",
        value=f"{running_bots}/{total_bots}",
        delta="Running" if running_bots > 0 else "All stopped",
        help="How many trading bots are currently working for you"
    )

with col2:
    pnl_color = "normal" if total_pnl >= 0 else "inverse"
    st.metric(
        label="💰 Total Profit" if beginner_mode else "Total P&L",
        value=f"${total_pnl:.2f}",
        delta=f"{(total_pnl/total_wallet)*100:.1f}%" if total_wallet > 0 else "0%",
        delta_color=pnl_color,
        help="Total money made or lost across all bots"
    )

with col3:
    st.metric(
        label="💵 Total Money" if beginner_mode else "Wallet Balance",
        value=f"${total_wallet:.2f}",
        help="Total amount of money available for trading"
    )

with col4:
    st.metric(
        label="🪙 Coins Owned" if beginner_mode else "Open Positions",
        value=total_positions,
        help="Number of different coins you currently own"
    )

with col5:
    st.metric(
        label="🔄 Total Trades" if beginner_mode else "Total Trades",
        value=total_trades_count,
        help="Total number of buy and sell actions completed"
    )

# Add helpful info box for beginners
if beginner_mode:
    st.markdown("""
    <div class="help-box">
        <strong>💡 What am I looking at?</strong><br>
        This shows a quick summary of all your trading bots. Each bot is like a little worker that buys and sells coins for you automatically!
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ===========================================
# ENHANCED BOT STATUS CARDS
# ===========================================
if beginner_mode:
    st.markdown("### 🤖 Your Trading Bots (Your Automatic Helpers)")
else:
    st.markdown("### 📊 Bot Status Dashboard")

if all_bot_status is not None and not all_bot_status.empty:
    # Display each bot as an enhanced card
    for idx, bot in all_bot_status.iterrows():
        # Get strategy explanation for beginners
        from dashboard.beginner_helpers import explain_strategy
        strategy_info = explain_strategy(bot['strategy'])

        # Status indicator
        if bot['status'] == 'RUNNING':
            status_emoji = "🟢"
            status_text = "WORKING" if beginner_mode else "RUNNING"
            status_class = "status-running"
        elif bot['status'] == 'READY':
            status_emoji = "🟡"
            status_text = "READY TO START" if beginner_mode else "READY"
            status_class = "status-running"
        else:
            status_emoji = "🔴"
            status_text = "STOPPED" if beginner_mode else "STOPPED"
            status_class = "status-stopped"

        # Create expandable card for each bot
        with st.expander(f"{status_emoji} **{strategy_info['simple_name'] if beginner_mode else bot['strategy']}** - {status_text}", expanded=(idx < 2)):
            if beginner_mode:
                # Show simple explanation first
                st.markdown(f"""
                <div class="help-box">
                    <strong>🎯 What this bot does:</strong> {strategy_info['what_it_does']}<br>
                    <strong>💡 {strategy_info['analogy']}</strong>
                </div>
                """, unsafe_allow_html=True)

            # Metrics in columns
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"<div style='text-align: center;'><span class='status-badge {status_class}'>{status_emoji} {status_text}</span></div>", unsafe_allow_html=True)
                st.caption("Bot Status" if not beginner_mode else "Working?")

            with col2:
                pnl = bot['total_pnl']
                pnl_emoji = "📈" if pnl >= 0 else "📉"
                st.metric(
                    "Money Made" if beginner_mode else "Total P&L",
                    f"${pnl:.2f}",
                    delta=f"{(pnl/bot['wallet_balance'])*100:.1f}%" if bot['wallet_balance'] > 0 else "0%",
                    delta_color="normal" if pnl >= 0 else "inverse"
                )

            with col3:
                st.metric(
                    "Money Available" if beginner_mode else "Wallet Balance",
                    f"${bot['wallet_balance']:.2f}",
                    help="Money this bot can use to buy coins"
                )

            with col4:
                st.metric(
                    "Trades Done" if beginner_mode else "Total Trades",
                    bot['total_trades'],
                    help="How many times this bot bought or sold"
                )

            # Additional details in a subtle way
            if not beginner_mode:
                st.caption(f"⏰ Started: {bot['started_at']} | Last Update: {bot['last_heartbeat']}")
            else:
                # Show when bought/sold info
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption(f"📅 **When it buys:** {strategy_info['when_it_buys']}")
                with col_b:
                    st.caption(f"💵 **When it sells:** {strategy_info['when_it_sells']}")

                # Risk level
                st.caption(f"⚠️ **Risk level:** {strategy_info['risk_level']}")
else:
    if beginner_mode:
        st.info("🤖 No trading bots are active yet. Don't worry - this dashboard will show your bots when they start working!")
    else:
        st.info("No bots running. Start a bot using `run_bot.py` on the VPS.")

st.markdown("---")



st.markdown("---")

# Tabs with beginner-friendly names
if beginner_mode:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💰 My Coins",
        "🎯 Safety Scores",
        "📜 Trade History",
        "📊 Price Charts",
        "🔭 New Coins",
        "🧠 Advanced"
    ])
else:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Open Positions",
        "🔍 Confluence V2",
        "📜 Trade History",
        "📊 Market Overview",
        "🔭 Watchlist Review",
        "🧠 Intelligence"
    ])

with tab1:
    if beginner_mode:
        st.subheader("💰 Your Coins (What You Own)")
        st.info("💡 **What is this?** These are the coins you currently own. The bot will automatically sell them when the price reaches your profit target!")
    else:
        st.subheader("Open Positions (FIFO)")
    
    open_positions = logger.get_open_positions()
    
    if not open_positions.empty:
        # Calculate unrealized P&L
        positions_display = open_positions.copy()
        positions_display['current_price'] = 0.0
        positions_display['unrealized_pnl'] = 0.0
        positions_display['unrealized_pnl_pct'] = 0.0
        
        for idx, row in positions_display.iterrows():
            try:
                ticker = exchange.fetch_ticker(row['symbol'])
                current_price = ticker['last']
                positions_display.at[idx, 'current_price'] = current_price
                
                unrealized_pnl = (current_price - row['buy_price']) * row['amount']
                positions_display.at[idx, 'unrealized_pnl'] = unrealized_pnl
                positions_display.at[idx, 'unrealized_pnl_pct'] = (unrealized_pnl / row['cost']) * 100
            except:
                pass
        
        if beginner_mode:
            # BEGINNER MODE: Show each position as a simple card
            for idx, pos in positions_display.iterrows():
                pnl_pct = pos['unrealized_pnl_pct']
                pnl_usd = pos['unrealized_pnl']
                
                # Get signal assessment (not prescriptive command)
                sig = get_signal_assessment(confluence_score=50, position_pnl_pct=pnl_pct)
                
                with st.expander(f"{sig['emoji']} {pos['symbol']} - {sig['simple_status']}", expanded=(abs(pnl_pct) > 5)):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"### 📊 Position Details")
                        st.write(f"**You bought at:** {format_dollar_amount(pos['buy_price'])}")
                        st.write(f"**Price now:** {format_dollar_amount(pos['current_price'])}")
                        st.write(f"**Amount you own:** {pos['amount']:.4f} {pos['symbol'].split('/')[0]}")
                        st.write(f"**Total invested:** {format_dollar_amount(pos['cost'])}")
                        
                        st.markdown("---")
                        st.markdown(f"### 💬 What The System Sees")
                        st.info(sig['what_system_sees'])
                        
                        st.markdown("### 🤔 Considerations")
                        st.caption(sig['considerations'])
                    
                    with col2:
                        st.markdown(f"### {sig['emoji']} Signal Status")
                        st.markdown(f"**{sig['signal_strength']}**")
                        
                        # Show current P&L
                        if pnl_usd >= 0:
                            st.success(f"Current: {format_dollar_amount(pnl_usd, show_sign=True)} ({pnl_pct:+.1f}%)")
                        else:
                            st.error(f"Current: {format_dollar_amount(pnl_usd)} ({pnl_pct:.1f}%)")
                        
                        # Show buy time
                        st.markdown("---")
                        st.caption(f"Bought: {pos['buy_timestamp']}")
                        st.caption(f"Strategy: {pos['strategy']}")
        else:
            # TECHNICAL MODE: Show table
            st.dataframe(
                positions_display[['symbol', 'strategy', 'buy_price', 'current_price', 'amount', 'cost', 'unrealized_pnl', 'unrealized_pnl_pct', 'buy_timestamp']],
                width='stretch',
                column_config={
                    "buy_price": st.column_config.NumberColumn("Buy Price", format="$%.4f"),
                    "current_price": st.column_config.NumberColumn("Current Price", format="$%.4f"),
                    "cost": st.column_config.NumberColumn("Cost", format="$%.2f"),
                    "unrealized_pnl": st.column_config.NumberColumn("Unrealized P&L", format="$%.2f"),
                    "unrealized_pnl_pct": st.column_config.NumberColumn("P&L %", format="%.2f%%"),
                }
            )
        
        # Summary
        total_cost = positions_display['cost'].sum()
        total_unrealized = positions_display['unrealized_pnl'].sum()
        
        if beginner_mode:
            st.markdown("---")
            st.markdown("### 📊 Total Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Invested", format_dollar_amount(total_cost))
            with col2:
                profit_color = "normal" if total_unrealized >= 0 else "inverse"
                st.metric("Total Profit/Loss", format_dollar_amount(total_unrealized, show_sign=True), 
                         delta=f"{(total_unrealized/total_cost)*100:.2f}%", delta_color=profit_color)
            with col3:
                current_value = total_cost + total_unrealized
                st.metric("Current Value", format_dollar_amount(current_value))
        else:
            st.metric("Total Unrealized P&L", f"${total_unrealized:.2f}", delta=f"{(total_unrealized/total_cost)*100:.2f}%")
    else:
        if beginner_mode:
            st.info("🛒 You don't own any coins yet. The bot will buy when it finds good opportunities!")
        else:
            st.info("No open positions. The bot will buy when conditions are met.")

with tab2:
    if beginner_mode:
        st.subheader("🎯 Safety Scores (Is It Safe to Buy?)")
        st.info("💡 **What is this?** The Safety Score tells you how safe it is to buy a coin right now. Higher scores = safer buys!")
    else:
        st.subheader("Confluence Engine V2 Monitoring")
    
    # Get all available symbols from history
    session = logger.db.get_session()
    from core.database import ConfluenceScore
    available_symbols_raw = session.query(ConfluenceScore.symbol).distinct().all()
    session.close()
    
    available_symbols = [s[0].split('/')[0] for s in available_symbols_raw if s[0]] if available_symbols_raw else ["BTC", "ETH", "SOL"]
    available_symbols = sorted(list(set(available_symbols)))
    
    symbol_to_monitor = st.selectbox("Select Coin for Scoring History", available_symbols, index=available_symbols.index("BTC") if "BTC" in available_symbols else 0)
    
    # Get latest scores
    scores_df = logger.get_latest_confluence_scores(symbol=f"{symbol_to_monitor}/USDT", limit=20)
    
    if not scores_df.empty:
        latest_score = scores_df.iloc[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Gauge for current score
            score_val = latest_score['total_score']
            v1_score = latest_score.get('v1_score', score_val) # Fallback if missing
            
            if beginner_mode:
                # Simple traffic light display
                emoji, status, message = get_traffic_light(score_val)
                st.markdown(f"### {emoji} Safety Score: {score_val}/100")
                st.success(f"**{status}**")
                st.info(f"💬 {message}")
                
                # Signal assessment (not command)
                sig = get_signal_assessment(score_val)
                st.markdown("---")
                st.markdown(f"### {sig['emoji']} Signal Assessment")
                st.markdown(f"**{sig['signal_strength']}**")
                st.caption(f"**What System Sees:** {sig['what_system_sees']}")
                st.caption(f"**Considerations:** {sig['considerations']}")
            else:
                # Technical gauge
                fig_score = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = score_val,
                    delta = {'reference': v1_score, 'relative': False, 'increasing': {'color': "green"}},
                    title = {'text': f"Latest V2 Score: {symbol_to_monitor}", 'font': {'size': 20}},
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "gold" if score_val > 50 else "gray"},
                        'steps': [
                            {'range': [0, 40], 'color': "rgba(255, 0, 0, 0.2)"},
                            {'range': [40, 60], 'color': "rgba(255, 255, 0, 0.2)"},
                            {'range': [60, 100], 'color': "rgba(0, 255, 0, 0.2)"}
                        ]
                    }
                ))
                fig_score.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
                st.plotly_chart(fig_score, use_container_width=True)
            
            # Show penalty info
            if not beginner_mode:
                penalty = latest_score.get('redundancy_penalty', 1.0)
                if penalty < 1.0:
                    st.warning(f"⚠️ Redundancy Penalty: **{penalty:.2f}x** (Signal Overlap detected)")
                else:
                    st.success("✅ Signal Independence: 100%")

        with col2:
            st.write("**Score Breakdown**")
            # Horizontal Bar Chart for categories
            # Mocking categories as they are often derived but we can show technical vs final
            breakdown_data = {
                'Metric': ['Technical', 'On-Chain', 'Macro', 'Fundamental', 'V1 Total', 'V2 FINAL'],
                'Score': [
                    latest_score.get('technical_score', 0),
                    latest_score.get('onchain_score', 0),
                    latest_score.get('macro_score', 0),
                    latest_score.get('fundamental_score', 0),
                    v1_score,
                    score_val
                ]
            }
            breakdown_df = pd.DataFrame(breakdown_data)
            fig_bar = go.Figure(go.Bar(
                x=breakdown_df['Score'],
                y=breakdown_df['Metric'],
                orientation='h',
                marker_color=['blue', 'blue', 'blue', 'blue', 'orange', 'gold']
            ))
            fig_bar.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), xaxis_range=[0, 100])
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.write("**Historical Calibration (V1 vs V2)**")
        
        # Plot V1 vs V2 Comparison
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Scatter(x=scores_df['timestamp'], y=scores_df['v1_score'], name='V1 (Raw)', line=dict(color='gray', dash='dot')))
        fig_comp.add_trace(go.Scatter(x=scores_df['timestamp'], y=scores_df['total_score'], name='V2 (Hardened)', line=dict(color='gold', width=3)))
        
        # Add a "Veto Zone" where score is low
        fig_comp.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Trade Veto Threshold")
        
        fig_comp.update_layout(height=350, title="V1 vs V2 Scoring Stability", hovermode='x unified')
        st.plotly_chart(fig_comp, use_container_width=True)
        
        st.dataframe(scores_df.head(10))
    else:
        st.info(f"No score history for {symbol_to_monitor}. Bot calibration in progress.")

    st.divider()
    st.subheader("🔭 Discovery History (New Listings)")
    # Show ALL recent scans across all symbols, focus on high scores
    all_recent_scans = logger.get_latest_confluence_scores(limit=15)
    if not all_recent_scans.empty:
        # Display with high-score highlighting
        st.dataframe(
            all_recent_scans[['timestamp', 'symbol', 'total_score', 'recommendation', 'regime_state', 'exchange']],
            width='stretch',
            column_config={
                "total_score": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%d"),
                "recommendation": st.column_config.TextColumn("Action")
            }
        )
    else:
        st.info("No discovery scans yet. The monitor runs every 30 minutes.")

with tab3:
    st.subheader("Trade History")
    
    trades = logger.get_trades()
    
    if not trades.empty:
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            symbol_filter = st.multiselect("Filter by Symbol", options=trades['symbol'].unique())
        with col2:
            side_filter = st.multiselect("Filter by Side", options=['BUY', 'SELL'])
        
        # Apply filters
        filtered_trades = trades.copy()
        if symbol_filter:
            filtered_trades = filtered_trades[filtered_trades['symbol'].isin(symbol_filter)]
        if side_filter:
            filtered_trades = filtered_trades[filtered_trades['side'].isin(side_filter)]
        
        st.dataframe(
            filtered_trades,
            width='stretch',
            column_config={
                "price": st.column_config.NumberColumn("Price", format="$%.4f"),
                "cost": st.column_config.NumberColumn("Cost", format="$%.2f"),
                "fee": st.column_config.NumberColumn("Fee", format="$%.4f"),
            }
        )
        
        # Download button
        csv = filtered_trades.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, "trades.csv", "text/csv")
    else:
        st.info("No trades executed yet. The bot is monitoring the market.")

with tab4:
    st.subheader("Market Overview")
    
    # Symbol selector
    all_symbols = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
        "DOGE/USDT", "ADA/USDT", "LINK/USDT", "TRX/USDT", "AVAX/USDT"
    ]
    
    selected_symbol = st.selectbox("Select Symbol", all_symbols)
    
    with st.spinner(f"Fetching {selected_symbol} data..."):
        df = exchange.fetch_ohlcv(selected_symbol, timeframe='1h', limit=100)
    
    if not df.empty:
        # Get trades for this symbol
        symbol_trades = trades[trades['symbol'] == selected_symbol] if not trades.empty else None
        
        # Get Grid Data for Visualization
        grid_data = None
        try:
            health_df = logger.get_system_health()
            if not health_df.empty:
                # Find component matching "Strategy: ... (Symbol)"
                # We look for partial match since strategy name is variable
                for _, row in health_df.iterrows():
                    if f"Strategy:" in row['component'] and f"({selected_symbol})" in row['component']:
                        import json
                        grid_data = json.loads(row['metrics_json'])
                        break
        except:
            pass

        plot_candle_chart(df, symbol_trades, title=f"{selected_symbol} Price Action", grid_data=grid_data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${df['close'].iloc[-1]:.4f}")
        with col2:
            change_24h = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24]) * 100
            st.metric("24h Change", f"{change_24h:.2f}%")
        with col3:
            st.metric("Volume", f"${df['volume'].iloc[-1]:,.0f}")

with tab5:
    st.subheader("🔭 Pillar C: New Coin Watchlist Review")
    
    # 1. Review Queue (Coins that reached Day 30)
    st.write("### 📋 Review Queue (Ready for Activation)")
    review_queue = logger.get_new_coin_watchlist(status='MANUAL_REVIEW')
    
    if not review_queue.empty:
        for idx, coin in review_queue.iterrows():
            with st.expander(f"⭐ {coin['symbol']} - {coin['classification']} ({coin['coin_age_days']} days old)", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**30-Day Performance Dossier**")
                    perf_cols = st.columns(3)
                    perf_cols[0].metric("Initial Price", f"${coin['initial_price']:.4f}")
                    perf_cols[1].metric("Current Price", f"${coin['day_30_price']:.4f}")
                    growth = ((coin['day_30_price'] - coin['initial_price']) / coin['initial_price']) * 100
                    perf_cols[2].metric("Growth", f"{growth:+.2f}%")
                    
                    st.write(f"**Max Drawdown:** `{coin['max_drawdown_pct']:.2f}%` | **Risk Level:** `{coin['risk_level']}`")
                    
                    # Research Links
                    base_sym = coin['symbol'].split('/')[0]
                    st.write("**Research Links:**")
                    l1, l2, l3 = st.columns(3)
                    l1.link_button("📊 MEXC Chart", f"https://www.mexc.com/exchange/{base_sym}_USDT")
                    l2.link_button("🛡️ DEXTools Audit", f"https://www.dextools.io/app/en/search?q={base_sym}")
                    l3.link_button("🦎 CoinGecko", f"https://www.coingecko.com/en/search_queries?search={base_sym}")
                
                with col2:
                    st.write("**Activation Control**")
                    with st.form(key=f"activate_{coin['symbol']}"):
                        notes = st.text_area("Research Notes", placeholder="e.g. Strong team, Certik audit passed...")
                        allocation = st.number_input("Wallet Amount (USD)", min_value=10.0, max_value=1000.0, value=100.0, step=10.0)
                        
                        btn_col1, btn_col2 = st.columns(2)
                        if btn_col1.form_submit_button("✅ ACTIVATE"):
                            if logger.activate_new_coin(coin['symbol'], allocation, notes):
                                st.success(f"Activated {coin['symbol']} for trading!")
                                st.rerun()
                        if btn_col2.form_submit_button("❌ REJECT"):
                            if logger.delete_watchlist_coin(coin['symbol']):
                                st.warning(f"Rejected {coin['symbol']}.")
                                st.rerun()
    else:
        st.info("The Review Queue is empty. Coins will appear here after surviving their 30-day monitoring phase.")

    st.divider()
    
    # 2. Monitoring List (In the Waiting Room)
    st.write("### ⏳ Waiting Room (Monitoring Phase)")
    monitoring_list = logger.get_new_coin_watchlist(status='MONITORING')
    
    if not monitoring_list.empty:
        # Format detected_at for display
        monitoring_display = monitoring_list.copy()
        # column selection
        cols = ['symbol', 'coin_type', 'coin_age_days', 'risk_level', 'initial_price', 'initial_volume_24h', 'detected_at']
        st.dataframe(
            monitoring_display[cols],
            width='stretch',
            column_config={
                "initial_price": st.column_config.NumberColumn("List Price", format="$%.4f"),
                "initial_volume_24h": st.column_config.NumberColumn("List Volume", format="$%.0f"),
                "detected_at": st.column_config.DatetimeColumn("Detected"),
                "coin_type": st.column_config.TextColumn("Type")
            }
        )
    else:
        st.info("No coins currently in the waiting room. The monitor scans MEXC every 30 minutes.")

st.markdown("---")

# Performance Analysis Section
st.subheader("🏆 Performance Analysis")

if not trades.empty:
    # Calculate P&L per symbol
    # We need to join trades with positions or just use closed trades profit
    # Since trades table doesn't have 'profit' column directly (it's in positions), 
    # we should query positions table for this analysis.
    
    # conn = logger.get_connection() # Helper needed or just direct connect
    # Let's use pandas to read positions directly
    import sqlite3
    conn = sqlite3.connect(logger.db_path)
    closed_positions = pd.read_sql_query("SELECT * FROM positions WHERE status = 'CLOSED'", conn)
    conn.close()
    
    if not closed_positions.empty:
        # Group by symbol AND strategy for proper attribution
        symbol_strategy_pnl = closed_positions.groupby(['symbol', 'strategy']).agg({
            'unrealized_pnl_usd': 'sum',
            'id': 'count'  # Number of trades
        }).reset_index()
        symbol_strategy_pnl.columns = ['symbol', 'strategy', 'total_pnl', 'num_trades']
        symbol_strategy_pnl = symbol_strategy_pnl.sort_values('total_pnl', ascending=False)
        
        # Also calculate overall symbol performance (across all strategies)
        symbol_pnl_total = closed_positions.groupby('symbol')['unrealized_pnl_usd'].sum().sort_values(ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("🚀 Top Performing Coins")
            # Show only coins with POSITIVE P&L
            top_performers = symbol_strategy_pnl[symbol_strategy_pnl['total_pnl'] > 0].head(5)
            
            if not top_performers.empty:
                for _, row in top_performers.iterrows():
                    profit_color = "🟢" if row['total_pnl'] > 0 else "🔴"
                    st.metric(
                        f"{row['symbol']} ({row['strategy'][:15]}...)", 
                        f"${row['total_pnl']:.2f}",
                        delta=f"{row['num_trades']} trades"
                    )
                    
                # Show total across all strategies
                st.caption(f"💰 Best Overall: {symbol_pnl_total.index[0]} (${symbol_pnl_total.iloc[0]:.2f})")
            else:
                st.info("No profitable coins yet")
                
        with col2:
            st.error("📉 Weakest Links")
            # Show only coins with NEGATIVE or lowest positive P&L
            worst_performers = symbol_strategy_pnl[symbol_strategy_pnl['total_pnl'] <0].head(5)
            
            # If no negative performers, show lowest positive ones (but not duplicates from top)
            if worst_performers.empty:
                worst_performers = symbol_strategy_pnl[symbol_strategy_pnl['total_pnl'] > 0].tail(5)
                worst_performers = worst_performers[~worst_performers.index.isin(top_performers.index)]
            
            if not worst_performers.empty:
                for _, row in worst_performers.iterrows():
                    profit_color = "🟢" if row['total_pnl'] > 0 else "🔴"
                    st.metric(
                        f"{row['symbol']} ({row['strategy'][:15]}...)", 
                        f"${row['total_pnl']:.2f}",
                        delta=f"{row['num_trades']} trades"
                    )
                    
                # Show worst overall
                if symbol_pnl_total.iloc[-1] < 0:
                    st.caption(f"⚠️ Worst Overall: {symbol_pnl_total.index[-1]} (${symbol_pnl_total.iloc[-1]:.2f})")
            else:
                st.success("All coins are profitable! 🎉")
                
    else:
        st.info("No closed positions yet to analyze performance.")
else:
    st.info("Waiting for trade data...")

with tab6:
    st.subheader("🧠 Multi-Asset Intelligence")
    st.info("Routes assets to either 'Confluence V2' (Technical) or 'Regulatory Scorer' (Fundamental).")
    
    # Initialize Engine
    engine = MasterDecisionEngine()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🏛️ Regulatory Assets")
        st.caption("Driven by: SEC status, ETF flows, Partnerships")
        
        regulatory_assets = ['XRP/USDT', 'ADA/USDT', 'SOL/USDT', 'MATIC/USDT', 'LINK/USDT', 'DOT/USDT']
        
        for symbol in regulatory_assets:
            result = engine.get_signal(symbol)
            
            with st.expander(f"{symbol} - {result['recommendation']}", expanded=(symbol == 'XRP/USDT')):
                # Score Gauge
                score = result.get('total_score', 0)
                
                # Determine color
                delta_color = "normal" if result['recommendation'] in ['BUY', 'STRONG_BUY'] else "inverse"
                st.metric("Total Score", f"{score}/100", delta=result['recommendation'], delta_color=delta_color)
                
                if 'breakdown' in result:
                     bd = result['breakdown']
                     st.write("**Score Components:**")
                     # Update denominators to match new weights (Reg 25, Inst 35, Eco 30, Mkt 10) + Safety Clamp
                     st.progress(min(bd.get('regulatory', 0) / 25, 1.0), text=f"Regulatory: {bd.get('regulatory', 0)}/25")
                     st.progress(min(bd.get('institutional', 0) / 35, 1.0), text=f"Institutional: {bd.get('institutional', 0)}/35")
                     st.progress(min(bd.get('ecosystem', 0) / 30, 1.0), text=f"Ecosystem: {bd.get('ecosystem', 0)}/30")
                     st.progress(min(bd.get('market', 0) / 10, 1.0), text=f"Market: {bd.get('market', 0)}/10")

    with col2:
        st.subheader("🧪 Technical Assets")
        st.caption("Driven by: RSI, MA Crossovers, Volume")
        
        technical_assets = ['BTC/USDT', 'ETH/USDT', 'DOGE/USDT', 'LTC/USDT', 'BCH/USDT']
        
        for symbol in technical_assets:
            with st.expander(f"{symbol}", expanded=False):
                st.info("Routed to: **Confluence V2 (Technical)**")
                st.write("Scoring Criteria:")
                st.markdown("- **Technical (30pts):** RSI, MACD")
                st.markdown("- **Trend (30pts):** SMA200, BTC Correlation")
                st.markdown("- **Volume (20pts):** Spike Detection")
                st.markdown("- **Sentiment (20pts):** CryptoPanic News")
                
                st.warning("To see live technical scores, use the 'Confluence V2' tab.")

    st.markdown("---")
    st.subheader("🔍 Asset Scorer Comparison Utility")

    selected_asset = st.text_input("Enter Asset Symbol (e.g. XRP/USDT)", "XRP/USDT")

    if st.button("Analyze Asset"):
        with st.spinner(f"Analyzing {selected_asset}..."):
            result = engine.get_signal(selected_asset)
            
            c1, c2, c3 = st.columns(3)
            # Use safe get() or standardized keys
            c1.metric("Classification", result.get('classification', result.get('asset_type', 'Unknown')))
            c2.metric("Used Scorer", result.get('scorer_used', 'Unknown'))
            c3.metric("Final Score", f"{result.get('total_score', 0)}/100")
            
            st.json(result)

# Auto-refresh
st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
if auto_refresh:
    time.sleep(30)
    st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("🤖 Crypto Trading Bot v2.0")
st.sidebar.caption("Running in Paper Trading Mode")
