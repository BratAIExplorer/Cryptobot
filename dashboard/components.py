import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_candle_chart(df, trades=None, title="Price Chart"):
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
            
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=sells['timestamp'], y=sells['price'],
                mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'),
                name='Sell'
            ), row=1, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True) # Keeping it for now as 'width' might be 1.56+ only

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
