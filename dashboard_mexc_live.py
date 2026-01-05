#!/usr/bin/env python3
"""
Streamlit Dashboard for MEXC LIVE Trading Bot
Real-time monitoring of live trades with safety indicators

Run: streamlit run dashboard_mexc_live.py --server.port 8501
"""
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os

# Page config
st.set_page_config(
    page_title="🔴 MEXC LIVE Trading Dashboard",
    page_icon="🔴",
    layout="wide"
)

# Database path
DB_PATH = 'data/trades_mexc_live.db'

def load_data():
    """Load data from live trading database"""
    if not os.path.exists(DB_PATH):
        st.error(f"❌ Database not found: {DB_PATH}")
        st.info("Start the bot first: python run_bot_mexc_SAFE_LIVE.py")
        return None, None, None

    conn = sqlite3.connect(DB_PATH)

    # Load trades
    trades_df = pd.read_sql_query("""
        SELECT * FROM trades
        ORDER BY timestamp DESC
        LIMIT 100
    """, conn)

    # Load positions
    positions_df = pd.read_sql_query("""
        SELECT * FROM positions
        ORDER BY entry_date DESC
    """, conn)

    # Load bot status
    try:
        bot_status_df = pd.read_sql_query("SELECT * FROM bot_status", conn)
    except:
        bot_status_df = pd.DataFrame()

    conn.close()

    return trades_df, positions_df, bot_status_df

def calculate_metrics(trades_df, positions_df):
    """Calculate key performance metrics"""
    metrics = {}

    if not trades_df.empty:
        # Total trades
        metrics['total_trades'] = len(trades_df)

        # Buy/Sell breakdown
        metrics['buys'] = len(trades_df[trades_df['side'] == 'BUY'])
        metrics['sells'] = len(trades_df[trades_df['side'] == 'SELL'])

        # Total P&L (from closed positions)
        if not positions_df.empty:
            closed = positions_df[positions_df['status'] == 'CLOSED']
            if not closed.empty and 'unrealized_pnl_usd' in closed.columns:
                metrics['total_pnl'] = closed['unrealized_pnl_usd'].sum()
                metrics['win_rate'] = (closed['unrealized_pnl_usd'] > 0).sum() / len(closed) * 100
            else:
                metrics['total_pnl'] = 0
                metrics['win_rate'] = 0
        else:
            metrics['total_pnl'] = 0
            metrics['win_rate'] = 0

        # Open positions
        if not positions_df.empty:
            open_positions = positions_df[positions_df['status'] == 'OPEN']
            metrics['open_positions'] = len(open_positions)
            if not open_positions.empty and 'unrealized_pnl_usd' in open_positions.columns:
                metrics['unrealized_pnl'] = open_positions['unrealized_pnl_usd'].sum()
            else:
                metrics['unrealized_pnl'] = 0
        else:
            metrics['open_positions'] = 0
            metrics['unrealized_pnl'] = 0

    else:
        metrics = {
            'total_trades': 0,
            'buys': 0,
            'sells': 0,
            'total_pnl': 0,
            'win_rate': 0,
            'open_positions': 0,
            'unrealized_pnl': 0
        }

    return metrics

# Main dashboard
st.title("🔴 MEXC LIVE TRADING DASHBOARD")
st.markdown("**⚠️ Real Money Trading - Monitor Closely!**")

# Auto-refresh
if st.button("🔄 Refresh Data") or True:
    trades_df, positions_df, bot_status_df = load_data()

    if trades_df is not None:
        metrics = calculate_metrics(trades_df, positions_df)

        # Top metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total P&L", f"${metrics['total_pnl']:.2f}")

        with col2:
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")

        with col3:
            st.metric("Total Trades", metrics['total_trades'])

        with col4:
            st.metric("Open Positions", metrics['open_positions'])

        with col5:
            st.metric("Unrealized P&L", f"${metrics['unrealized_pnl']:.2f}")

        # Capital allocation status
        st.markdown("---")
        st.subheader("💰 Capital Allocation")

        if not positions_df.empty:
            # Calculate capital used per bot
            open_pos = positions_df[positions_df['status'] == 'OPEN']
            if not open_pos.empty and 'bot_id' in open_pos.columns:
                capital_by_bot = open_pos.groupby('bot_id')['position_size_usd'].sum().reset_index()
                capital_by_bot.columns = ['Bot', 'Capital Used ($)']

                col1, col2 = st.columns([2, 1])
                with col1:
                    st.dataframe(capital_by_bot, use_container_width=True)

                with col2:
                    total_used = capital_by_bot['Capital Used ($)'].sum()
                    total_allocated = 140  # From config
                    utilization = (total_used / total_allocated * 100) if total_allocated > 0 else 0

                    st.metric("Total Allocated", f"${total_allocated:.2f}")
                    st.metric("Currently Used", f"${total_used:.2f}")
                    st.metric("Utilization", f"{utilization:.1f}%")

        # Open positions
        st.markdown("---")
        st.subheader("📊 Open Positions")

        if not positions_df.empty:
            open_positions = positions_df[positions_df['status'] == 'OPEN']
            if not open_positions.empty:
                # Select relevant columns
                display_cols = ['bot_id', 'symbol', 'entry_price', 'current_price',
                               'unrealized_pnl_pct', 'unrealized_pnl_usd', 'entry_date']

                available_cols = [col for col in display_cols if col in open_positions.columns]
                display_df = open_positions[available_cols].copy()

                # Format columns
                if 'entry_price' in display_df.columns:
                    display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:.4f}")
                if 'current_price' in display_df.columns:
                    display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.4f}")
                if 'unrealized_pnl_pct' in display_df.columns:
                    display_df['unrealized_pnl_pct'] = display_df['unrealized_pnl_pct'].apply(lambda x: f"{x:.2f}%")
                if 'unrealized_pnl_usd' in display_df.columns:
                    display_df['unrealized_pnl_usd'] = display_df['unrealized_pnl_usd'].apply(lambda x: f"${x:.2f}")

                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("No open positions")
        else:
            st.info("No positions data available")

        # Recent trades
        st.markdown("---")
        st.subheader("📈 Recent Trades")

        if not trades_df.empty:
            # Select relevant columns
            display_cols = ['timestamp', 'side', 'symbol', 'price', 'amount', 'strategy']
            available_cols = [col for col in display_cols if col in trades_df.columns]
            recent_trades = trades_df[available_cols].head(20).copy()

            # Format columns
            if 'price' in recent_trades.columns:
                recent_trades['price'] = recent_trades['price'].apply(lambda x: f"${x:.4f}")
            if 'amount' in recent_trades.columns:
                recent_trades['amount'] = recent_trades['amount'].apply(lambda x: f"{x:.4f}")

            # Color code side
            def highlight_side(row):
                if 'side' not in row:
                    return [''] * len(row)
                if row['side'] == 'BUY':
                    return ['background-color: #90EE90'] * len(row)
                elif row['side'] == 'SELL':
                    return ['background-color: #FFB6C1'] * len(row)
                return [''] * len(row)

            st.dataframe(recent_trades.style.apply(highlight_side, axis=1), use_container_width=True)
        else:
            st.info("No trades yet")

        # Bot status
        st.markdown("---")
        st.subheader("🤖 Bot Status")

        if not bot_status_df.empty:
            status_display = bot_status_df[['bot_name', 'status', 'updated_at']].copy()
            st.dataframe(status_display, use_container_width=True)
        else:
            st.info("No bot status data")

        # Safety indicators
        st.markdown("---")
        st.subheader("🛡️ Safety Status")

        # Check for circuit breaker
        conn = sqlite3.connect(DB_PATH)
        try:
            cb_status = pd.read_sql_query("SELECT * FROM circuit_breaker LIMIT 1", conn)
            if not cb_status.empty:
                is_paused = cb_status['is_paused'].iloc[0]
                if is_paused:
                    st.error("🔴 CIRCUIT BREAKER ACTIVE - Trading Paused!")
                    st.info(f"Reason: {cb_status['reason'].iloc[0] if 'reason' in cb_status else 'Unknown'}")
                else:
                    st.success("✅ Circuit Breaker: OK")
            else:
                st.success("✅ Circuit Breaker: OK")
        except:
            st.info("Circuit breaker table not found")
        conn.close()

        # Daily P&L limit check
        conn = sqlite3.connect(DB_PATH)
        try:
            today = datetime.now().date()
            daily_pnl_query = f"""
                SELECT SUM(unrealized_pnl_usd) as daily_pnl
                FROM positions
                WHERE status='CLOSED'
                AND DATE(exit_time) = '{today}'
            """
            daily_pnl_df = pd.read_sql_query(daily_pnl_query, conn)
            if not daily_pnl_df.empty and daily_pnl_df['daily_pnl'].iloc[0] is not None:
                daily_pnl = daily_pnl_df['daily_pnl'].iloc[0]
                daily_limit = -50  # From config

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Today's P&L", f"${daily_pnl:.2f}")
                with col2:
                    st.metric("Daily Loss Limit", f"${daily_limit:.2f}")
                with col3:
                    remaining = daily_limit - daily_pnl
                    st.metric("Remaining Buffer", f"${abs(remaining):.2f}")

                if daily_pnl < daily_limit:
                    st.error(f"🚨 DAILY LOSS LIMIT HIT! (${daily_pnl:.2f} < ${daily_limit:.2f})")
            else:
                st.info("No trades today yet")
        except Exception as e:
            st.warning(f"Could not calculate daily P&L: {e}")
        conn.close()

        # Emergency controls
        st.markdown("---")
        st.subheader("🛑 Emergency Controls")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🛑 EMERGENCY STOP"):
                try:
                    with open('STOP_SIGNAL', 'w') as f:
                        f.write(str(datetime.now()))
                    st.success("✅ STOP_SIGNAL created! Bot will stop on next cycle.")
                except Exception as e:
                    st.error(f"Error creating STOP_SIGNAL: {e}")

        with col2:
            st.info("Manual Stop: `touch STOP_SIGNAL`")

        with col3:
            st.info("View Logs: `tail -f logs/live_*.log`")

        # Last updated
        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"Database: {DB_PATH}")

        # Auto-refresh every 30 seconds
        st.markdown("""
        <script>
            setTimeout(function() {
                window.location.reload();
            }, 30000);
        </script>
        """, unsafe_allow_html=True)

else:
    st.info("Click Refresh to load data")

# Sidebar
with st.sidebar:
    st.header("📋 Bot Configuration")
    st.markdown("""
    **Phase 1: Grid Bots Only**
    - BTC Grid: $80
    - ETH Grid: $60
    - Reserve: $78.08

    **Safety Limits:**
    - Daily Loss: -$50
    - Max Open Positions: 5

    **Emergency Stop:**
    ```bash
    touch STOP_SIGNAL
    ```

    **Monitor:**
    ```bash
    ./monitor_mexc_live.sh
    ```
    """)

    st.markdown("---")
    st.markdown("**⚠️ LIVE TRADING**")
    st.markdown("Monitor frequently!")
