import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_candle_chart(df, trades=None, title="Price Chart", grid_data=None):
    """
    Plot candlestick chart with optional trade markers.
    """
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=(title, 'Volume'), 
                        row_width=[0.2, 0.7])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='OHLC'
    ), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(
        x=df['timestamp'],
        y=df['volume'],
        name='Volume'
    ), row=2, col=1)

    # Add Trades
    if trades is not None and not trades.empty:
        buys = trades[trades['side'] == 'BUY']
        sells = trades[trades['side'] == 'SELL']
        
        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=buys['timestamp'], y=buys['price'],
                mode='markers', marker=dict(symbol='triangle-up', size=10, color='green'),
                name='Buy'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=sells['timestamp'], y=sells['price'],
                mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'),
                name='Sell'
            ), row=1, col=1)

    # Grid Lines
    if grid_data:
        # Plot Range Limits
        if grid_data.get('lower_limit'):
            fig.add_hline(y=grid_data['lower_limit'], line_dash="dash", line_color="green", opacity=0.7, row=1, col=1)
        if grid_data.get('upper_limit'):
            fig.add_hline(y=grid_data['upper_limit'], line_dash="dash", line_color="red", opacity=0.7, row=1, col=1)
            
        # Plot Levels (Optional: can be too busy if many levels)
        if grid_data.get('grid_levels'):
            for level in grid_data['grid_levels']:
                fig.add_hline(y=level, line_color="gray", opacity=0.2, row=1, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, width='stretch')

def strategy_config_ui():
    """
    UI for configuring strategies.
    Returns a dict with config values.
    """
    st.sidebar.header("Strategy Config")
    strategy_type = st.sidebar.selectbox("Select Strategy", ["DCA", "Grid", "SMA Crossover", "Hyper-Scalper", "Volatility Hunter"])
    
    top_15_coins = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
        "DOGE/USDT", "ADA/USDT", "LINK/USDT", "TRX/USDT", "AVAX/USDT",
        "SUI/USDT", "SEI/USDT", "NEAR/USDT", "APT/USDT", "INJ/USDT"
    ]
    
    use_all_coins = st.sidebar.checkbox("Select All Top 15 Coins", value=False)
    
    if use_all_coins:
        symbols = top_15_coins
        st.sidebar.info(f"Selected {len(symbols)} coins")
    else:
        symbols = st.sidebar.multiselect("Select Symbols", top_15_coins, default=["BTC/USDT"])

    amount = st.sidebar.number_input("Trade Amount per Coin (USD)", min_value=10, value=100)
    
    config = {
        'name': f"{strategy_type} Bot",
        'type': strategy_type,
        'symbols': symbols,
        'amount': amount
    }
    
    if strategy_type == "DCA":
        config['rsi_limit'] = st.sidebar.slider("RSI Limit (Buy below)", 10, 50, 30)
    elif strategy_type == "Grid":
        config['grid_levels'] = st.sidebar.slider("Grid Levels", 5, 50, 10)
        config['range_pct'] = st.sidebar.slider("Range %", 0.01, 0.5, 0.1)
    elif strategy_type == "SMA Crossover":
        config['fast_period'] = st.sidebar.number_input("Fast MA", value=50)
        config['slow_period'] = st.sidebar.number_input("Slow MA", value=200)
    elif strategy_type == "Hyper-Scalper":
        config['rsi_limit'] = st.sidebar.slider("RSI Limit (Aggressive)", 2, 20, 10)
        st.sidebar.info("Target Profit: 0.3% (Fixed)")
    elif strategy_type == "Volatility Hunter":
        config['volatility_threshold'] = st.sidebar.slider("Min Move % (5 min)", 0.01, 0.10, 0.02)
        
    return config

# ==================== NEW VISUALIZATION COMPONENTS ====================

def render_strategy_comparison(closed_positions):
    """Display strategy performance comparison table"""
    if closed_positions.empty:
        st.info("No closed positions yet")
        return
    
    # Aggregate by strategy
    strategy_stats = closed_positions.groupby('strategy').agg({
        'profit': ['sum', 'mean', 'count'],
    }).round(2)
    
    strategy_stats.columns = ['Total P&L', 'Avg P&L', 'Trades']
    
    # Calculate win rate
    win_rates = {}
    for strategy in closed_positions['strategy'].unique():
        strategy_positions = closed_positions[closed_positions['strategy'] == strategy]
        wins = (strategy_positions['profit'] > 0).sum()
        total = len(strategy_positions)
        win_rates[strategy] = (wins / total * 100) if total > 0 else 0
    
    strategy_stats['Win Rate %'] = strategy_stats.index.map(win_rates)
    
    # Sort by Total P&L
    strategy_stats = strategy_stats.sort_values('Total P&L', ascending=False)
    
    st.dataframe(
        strategy_stats,
        width='stretch',
        column_config={
            "Total P&L": st.column_config.NumberColumn("Total P&L", format="$%.2f"),
            "Avg P&L": st.column_config.NumberColumn("Avg P&L/Trade", format="$%.2f"),
            "Win Rate %": st.column_config.NumberColumn("Win Rate", format="%.1f%%"),
        }
    )

def render_pnl_chart(closed_positions):
    """Render cumulative P&L over time"""
    if closed_positions.empty:
        st.info("No data to display")
        return
    
    # Sort by sell timestamp
    df = closed_positions.sort_values('sell_timestamp').copy()
    df['cumulative_pnl'] = df['profit'].cumsum()
    
    fig = go.Figure()
    
    # Cumulative P&L line
    fig.add_trace(go.Scatter(
        x=df['sell_timestamp'],
        y=df['cumulative_pnl'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color='#00CC96', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 204, 150, 0.1)'
    ))
    
    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title="Cumulative P&L Over Time",
        xaxis_title="Date",
        yaxis_title="P&L ($)",
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, width='stretch')

def render_equity_curve(closed_positions, initial_balance=50000):
    """Render portfolio equity curve"""
    if closed_positions.empty:
        st.info("No data yet")
        return
    
    df = closed_positions.sort_values('sell_timestamp').copy()
    df['cumulative_pnl'] = df['profit'].cumsum()
    df['equity'] = initial_balance + df['cumulative_pnl']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['sell_timestamp'],
        y=df['equity'],
        mode='lines',
        name='Portfolio Equity',
        line=dict(color='#636EFA', width=3)
    ))
    
    # Starting balance line
    fig.add_hline(y=initial_balance, line_dash="dot", line_color="gray", 
                  annotation_text=f"Starting: ${initial_balance:,.0f}")
    
    fig.update_layout(
        title="Portfolio Equity Curve",
        xaxis_title="Date",
        yaxis_title="Equity ($)",
       height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, width='stretch')

def render_activity_feed(trades_df, limit=15):
    """Display recent trading activity"""
    if trades_df.empty:
        st.info("No recent activity")
        return
    
    recent = trades_df.head(limit).copy()
    
    for _, trade in recent.iterrows():
        icon = "🟢" if trade['side'] == 'BUY' else "🔴"
        col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
        
        with col1:
            st.write(icon)
        with col2:
            st.write(f"**{trade['symbol']}**")
        with col3:
            st.write(f"{trade['side']} @ ${trade['price']:.4f}")
        with col4:
            st.caption(str(trade['timestamp'])[:19])
