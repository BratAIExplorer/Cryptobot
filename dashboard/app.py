import streamlit as st
import pandas as pd
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.logger import TradeLogger
from dashboard.components import plot_candle_chart, strategy_config_ui
from core.exchange import ExchangeInterface

st.set_page_config(page_title="Crypto Bot Dashboard", layout="wide", page_icon="🤖")

st.title("🤖 Crypto Algo Trading Bot Dashboard")

# Initialize
logger = TradeLogger()
exchange = ExchangeInterface()

# Sidebar
st.sidebar.title("⚙️ Settings")
st.sidebar.info("The bot is running as a separate service. Use this dashboard to monitor performance.")

# Main Dashboard
st.subheader("📊 Active Bots")

# Get all bot statuses from database
all_bot_status = logger.get_bot_status()

if all_bot_status is not None and not all_bot_status.empty:
    # Display each bot as a card
    for idx, bot in all_bot_status.iterrows():
        with st.expander(f"🤖 {bot['strategy']}", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                status_color = "🟢" if bot['status'] == 'RUNNING' else "🔴"
                st.metric("Status", f"{status_color} {bot['status']}")
            
            with col2:
                st.metric("Total P&L", f"${bot['total_pnl']:.2f}",
                         delta=f"{(bot['total_pnl']/bot['wallet_balance'])*100:.2f}%" if bot['wallet_balance'] > 0 else "0%")
            
            with col3:
                st.metric("Wallet Balance", f"${bot['wallet_balance']:.2f}")
            
            with col4:
                st.metric("Total Trades", bot['total_trades'])
            
            # Additional info
            st.caption(f"Started: {bot['started_at']} | Last Update: {bot['last_heartbeat']}")
else:
    st.info("No bots running. Start a bot using `run_bot.py` on the VPS.")

st.markdown("---")



st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Open Positions", "📜 Trade History", "📊 Market Overview"])

with tab1:
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
        
        # Display
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
        st.metric("Total Unrealized P&L", f"${total_unrealized:.2f}", delta=f"{(total_unrealized/total_cost)*100:.2f}%")
    else:
        st.info("No open positions. The bot will buy when conditions are met.")

with tab2:
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

with tab3:
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
        
        plot_candle_chart(df, symbol_trades, title=f"{selected_symbol} Price Action")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${df['close'].iloc[-1]:.4f}")
        with col2:
            change_24h = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24]) * 100
            st.metric("24h Change", f"{change_24h:.2f}%")
        with col3:
            st.metric("Volume", f"${df['volume'].iloc[-1]:,.0f}")

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
            'profit': 'sum',
            'id': 'count'  # Number of trades
        }).reset_index()
        symbol_strategy_pnl.columns = ['symbol', 'strategy', 'total_pnl', 'num_trades']
        symbol_strategy_pnl = symbol_strategy_pnl.sort_values('total_pnl', ascending=False)
        
        # Also calculate overall symbol performance (across all strategies)
        symbol_pnl_total = closed_positions.groupby('symbol')['profit'].sum().sort_values(ascending=False)
        
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
