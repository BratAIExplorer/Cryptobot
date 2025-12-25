import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from intelligence.master_decision import MasterDecisionEngine

st.set_page_config(page_title="Intelligence Dashboard", layout="wide", page_icon="🧠")

st.title("🧠 Multi-Asset Intelligence Dashboard")
st.markdown("---")

# Initialize Engine
@st.cache_resource
def get_engine():
    return MasterDecisionEngine()

engine = get_engine()

# --- SIDEBAR ---
st.sidebar.header("Configuration")
st.sidebar.info("Routes assets to either 'Confluence V2' (Technical) or 'Regulatory Scorer' (Fundamental).")

# --- MAIN SECTION ---

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🏛️ Regulatory Assets (Fundamental)")
    st.caption("Driven by: SEC status, ETF flows, Partnerships")
    
    regulatory_assets = ['XRP/USDT', 'ADA/USDT', 'SOL/USDT', 'MATIC/USDT', 'LINK/USDT', 'DOT/USDT']
    
    for symbol in regulatory_assets:
        result = engine.get_signal(symbol)
        
        with st.expander(f"{symbol} - {result['recommendation']}", expanded=(symbol == 'XRP/USDT')):
            # Score Gauge
            score = result.get('total_score', 0)
            
            # Determine color
            if score >= 70: color = "green"
            elif score >= 50: color = "orange"
            else: color = "red"
            
            st.metric("Total Score", f"{score}/100", delta=result['recommendation'], delta_color="normal" if result['recommendation'] in ['BUY', 'STRONG_BUY'] else "inverse")
            
            if 'breakdown' in result:
                 bd = result['breakdown']
                 st.write("**Score Components:**")
                 st.progress(bd['regulatory'] / 40, text=f"Regulatory: {bd['regulatory']}/40")
                 st.progress(bd['institutional'] / 30, text=f"Institutional: {bd['institutional']}/30")
                 st.progress(bd['ecosystem'] / 20, text=f"Ecosystem: {bd['ecosystem']}/20")
                 st.progress(bd['market'] / 10, text=f"Market: {bd['market']}/10")

with col2:
    st.subheader("🧪 Technical Assets (Confluence V2)")
    st.caption("Driven by: RSI, MA Crossovers, Volume")
    
    technical_assets = ['BTC/USDT', 'ETH/USDT', 'DOGE/USDT', 'LTC/USDT', 'BCH/USDT']
    
    for symbol in technical_assets:
        # For now, we just show the routing status since we aren't fetching live market data in this view yet
        # In a real integration, we'd call ConfluenceFilter here
        
        with st.expander(f"{symbol}", expanded=False):
            st.info("Routed to: **Confluence V2 (Technical)**")
            st.write("Scoring Criteria:")
            st.markdown("- **Technical (30pts):** RSI, MACD")
            st.markdown("- **Trend (30pts):** SMA200, BTC Correlation")
            st.markdown("- **Volume (20pts):** Spike Detection")
            st.markdown("- **Sentiment (20pts):** CryptoPanic News")
            
            st.warning("To see live technical scores, use the main bot dashboard.")

st.markdown("---")
st.subheader("🔍 Asset Scorer Comparison Utility")

selected_asset = st.text_input("Enter Asset Symbol (e.g. XRP/USDT)", "XRP/USDT")

if st.button("Analyze Asset"):
    with st.spinner(f"Analyzing {selected_asset}..."):
        result = engine.get_signal(selected_asset)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Classification", result['classification'])
        c2.metric("Used Scorer", result['scorer'])
        c3.metric("Final Score", f"{result['total_score']}/100")
        
        st.json(result)

# Footer
st.markdown("---")
st.caption("CryptoIntel Hub - Intelligence Layer v1.0")
