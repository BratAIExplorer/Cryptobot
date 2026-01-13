"""
CryptoBots V3 - Streamlit Web Dashboard
Beautiful, modern web interface for monitoring and configuring the trading bot.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from config_manager import ConfigManager
from strategy_engine import StrategyEngine
from health_monitor import HealthMonitor
from bot_instance_manager import BotInstanceManager
from testnet_manager import TestnetManager
from trade_manager import TradeManager
from dashboard_panels import (
    render_trading_mode_selector,
    render_active_bots_panel,
    render_wallet_balance_panel,
    render_bot_creator_modal,
    render_quick_stats,
    render_trade_feed
)


# Page configuration
st.set_page_config(
    page_title="CryptoBots V3 Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium aesthetics
st.markdown("""
<style>
    /* Modern color scheme */
    :root {
        --primary-color: #6366f1;
        --success-color: #10b981;
        --danger-color: #ef4444;
        --warning-color: #f59e0b;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
        margin-bottom: 1rem;
    }
    
    /* Status indicators */
    .status-healthy { color: #10b981; font-weight: bold; }
    .status-warning { color: #f59e0b; font-weight: bold; }
    .status-critical { color: #ef4444; font-weight: bold; }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'config_manager' not in st.session_state:
    st.session_state.config_manager = ConfigManager()
    st.session_state.strategy_engine = StrategyEngine(st.session_state.config_manager)
    st.session_state.bot_manager = BotInstanceManager()
    st.session_state.testnet_manager = TestnetManager()
    st.session_state.trade_manager = TradeManager()
    st.session_state.trading_mode = 'testnet'
    st.session_state.show_bot_creator = False
    st.session_state.last_update = datetime.now()


def render_header():
    """Render the dashboard header."""
    st.markdown("""
        <div class="main-header">
            <h1>🤖 CryptoBots V3 Dashboard</h1>
            <p>Intelligent Crypto Trading with Health Monitoring & Proven Strategies</p>
        </div>
    """, unsafe_allow_html=True)


def render_health_status():
    """Render health monitoring status."""
    st.subheader("🏥 Health Monitor")
    
    engine = st.session_state.strategy_engine
    healthy = engine.run_health_check()
    
    health_data = engine.health_monitor.health_status
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        heartbeat = health_data.get('heartbeat', {})
        status = heartbeat.get('status', 'UNKNOWN')
        emoji = {'OK': '🟢', 'WARNING': '🟡', 'CRITICAL': '🔴', 'UNKNOWN': '⚪'}.get(status, '⚪')
        st.metric("Heartbeat", f"{emoji} {status}")
    
    with col2:
        api = health_data.get('api_connection', {})
        status = api.get('status', 'UNKNOWN')
        emoji = {'OK': '🟢', 'WARNING': '🟡', 'CRITICAL': '🔴', 'UNKNOWN': '⚪'}.get(status, '⚪')
        st.metric("API Status", f"{emoji} {status}")
    
    with col3:
        data = health_data.get('data_freshness', {})
        status = data.get('status', 'UNKNOWN')
        emoji = {'OK': '🟢', 'WARNING': '🟡', 'CRITICAL': '🔴', 'UNKNOWN': '⚪'}.get(status, '⚪')
        st.metric("Data Feed", f"{emoji} {status}")
    
    with col4:
        vitals = health_data.get('system_vitals', {})
        status = vitals.get('status', 'UNKNOWN')
        emoji = {'OK': '🟢', 'WARNING': '🟡', 'CRITICAL': '🔴', 'UNKNOWN': '⚪'}.get(status, '⚪')
        st.metric("System", f"{emoji} {status}")
    
    if health_data.get('emergency_stop', False):
        st.error("🚨 EMERGENCY STOP ACTIVATED - Trading Halted")


def render_performance_summary():
    """Render overall performance metrics."""
    st.subheader("📊 Performance Summary")
    
    engine = st.session_state.strategy_engine
    perf = engine.get_performance_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Trades",
            f"{perf['total_trades']}",
            delta=None
        )
    
    with col2:
        win_rate = perf['win_rate']
        st.metric(
            "Win Rate",
            f"{win_rate:.1f}%",
            delta=None
        )
    
    with col3:
        total_pnl = perf['total_pnl']
        st.metric(
            "Total P&L",
            f"${total_pnl:+,.2f}",
            delta=f"{total_pnl:+,.2f}"
        )
    
    with col4:
        st.metric(
            "Open Positions",
            f"{perf['open_positions']}",
            delta=None
        )


def render_strategy_config():
    """Render strategy configuration panel."""
    st.subheader("⚙️ Strategy Configuration")
    
    config = st.session_state.config_manager
    engine = st.session_state.strategy_engine
    
    # Create tabs for each strategy
    tab1, tab2, tab3 = st.tabs(["📉 Buy @ DIP", "💰 Take Profit", "📈 Trend Following"])
    
    with tab1:
        render_buy_dip_config(config, engine)
    
    with tab2:
        render_take_profit_config(config, engine)
    
    with tab3:
        render_trend_following_config(config, engine)


def render_buy_dip_config(config, engine):
    """Render Buy @ DIP strategy configuration."""
    strategy = engine.get_strategy('buy_dip')
    strategy_config = config.get_strategy_config('buy_dip')
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        enabled = st.checkbox(
            "Enable Strategy",
            value=strategy_config.get('enabled', True),
            key='buy_dip_enabled'
        )
        strategy.enable() if enabled else strategy.disable()
    
    with col2:
        st.markdown(f"**Status:** {'🟢 ENABLED' if enabled else '🔴 DISABLED'}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        dip_percent = st.slider(
            "Dip Trigger Percentage",
            min_value=1.0,
            max_value=15.0,
            value=strategy_config.get('dip_percentage', 5.0),
            step=0.5,
            help="Buy when price drops this % below 24h high",
            key='buy_dip_dip_percent'
        )
        
        position_size = st.slider(
            "Position Size (% of Balance)",
            min_value=1.0,
            max_value=25.0,
            value=strategy_config.get('position_size_percent', 10.0),
            step=1.0,
            key='buy_dip_position_size'
        )
    
    with col2:
        cooldown = st.slider(
            "Cooldown Period (hours)",
            min_value=1,
            max_value=24,
            value=strategy_config.get('cooldown_hours', 4),
            step=1,
            help="Minimum time between buys"
        )
        
        stop_loss = st.slider(
            "Stop Loss (%)",
            min_value=0.5,
            max_value=5.0,
            value=strategy_config.get('stop_loss_percent', 2.0),
            step=0.5
        )
    
    if st.button("💾 Save Buy @ DIP Config", key='save_buy_dip'):
        new_config = {
            'enabled': enabled,
            'dip_percentage': dip_percent,
            'cooldown_hours': cooldown,
            'position_size_percent': position_size,
            'stop_loss_percent': stop_loss
        }
        config.update_strategy_config('buy_dip', new_config)
        strategy.update_config(new_config)
        st.success("✅ Configuration saved!")


def render_take_profit_config(config, engine):
    """Render Take Profit strategy configuration."""
    strategy = engine.get_strategy('take_profit')
    strategy_config = config.get_strategy_config('take_profit')
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        enabled = st.checkbox(
            "Enable Strategy",
            value=strategy_config.get('enabled', True),
            key='take_profit_enabled'
        )
        strategy.enable() if enabled else strategy.disable()
    
    with col2:
        st.markdown(f"**Status:** {'🟢 ENABLED' if enabled else '🔴 DISABLED'}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        profit_target = st.slider(
            "Profit Target (%)",
            min_value=0.5,
            max_value=10.0,
            value=strategy_config.get('profit_target_percent', 3.0),
            step=0.5,
            help="Target profit percentage",
            key='take_profit_target'
        )
        
        trailing_stop = st.slider(
            "Trailing Stop (%)",
            min_value=0.1,
            max_value=3.0,
            value=strategy_config.get('trailing_stop_percent', 1.0),
            step=0.1,
            help="Trailing stop after profit target hit",
            key='take_profit_trailing'
        )
    
    with col2:
        stop_loss = st.slider(
            "Max Stop Loss (%)",
            min_value=0.5,
            max_value=5.0,
            value=strategy_config.get('stop_loss_percent', 2.0),
            step=0.5,
            key='take_profit_stop_loss'
        )
        
        position_size = st.slider(
            "Position Size (% of Balance)",
            min_value=1.0,
            max_value=25.0,
            value=strategy_config.get('position_size_percent', 10.0),
            step=1.0,
            key='take_profit_position_size'
        )
    
    if st.button("💾 Save Take Profit Config", key='save_take_profit'):
        new_config = {
            'enabled': enabled,
            'profit_target_percent': profit_target,
            'trailing_stop_percent': trailing_stop,
            'stop_loss_percent': stop_loss,
            'position_size_percent': position_size
        }
        config.update_strategy_config('take_profit', new_config)
        strategy.update_config(new_config)
        st.success("✅ Configuration saved!")


def render_trend_following_config(config, engine):
    """Render Trend Following strategy configuration."""
    strategy = engine.get_strategy('trend_following')
    strategy_config = config.get_strategy_config('trend_following')
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        enabled = st.checkbox(
            "Enable Strategy",
            value=strategy_config.get('enabled', False),
            key='trend_following_enabled'
        )
        strategy.enable() if enabled else strategy.disable()
    
    with col2:
        st.markdown(f"**Status:** {'🟢 ENABLED' if enabled else '🔴 DISABLED'}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fast_ma = st.slider(
            "Fast MA Period",
            min_value=10,
            max_value=100,
            value=strategy_config.get('fast_ma_period', 50),
            step=10,
            help="Fast moving average period",
            key='trend_fast_ma'
        )
        
        max_drawdown = st.slider(
            "Max Drawdown (%)",
            min_value=1.0,
            max_value=15.0,
            value=strategy_config.get('max_drawdown_percent', 5.0),
            step=0.5,
            key='trend_max_drawdown'
        )
    
    with col2:
        slow_ma = st.slider(
            "Slow MA Period",
            min_value=50,
            max_value=300,
            value=strategy_config.get('slow_ma_period', 200),
            step=10,
            help="Slow moving average period",
            key='trend_slow_ma'
        )
        
        position_size = st.slider(
            "Position Size (% of Balance)",
            min_value=1.0,
            max_value=30.0,
            value=strategy_config.get('position_size_percent', 15.0),
            step=1.0,
            key='trend_position_size'
        )
    
    if st.button("💾 Save Trend Following Config", key='save_trend_following'):
        new_config = {
            'enabled': enabled,
            'fast_ma_period': fast_ma,
            'slow_ma_period': slow_ma,
            'max_drawdown_percent': max_drawdown,
            'position_size_percent': position_size
        }
        config.update_strategy_config('trend_following', new_config)
        strategy.update_config(new_config)
        st.success("✅ Configuration saved!")


def render_bot_controls():
    """Render bot control buttons."""
    st.subheader("🎮 Bot Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ Start Bot", use_container_width=True):
            st.session_state.strategy_engine.start()
            st.success("Bot started!")
    
    with col2:
        if st.button("⏸️ Pause Bot", use_container_width=True):
            st.session_state.strategy_engine.stop()
            st.warning("Bot paused!")
    
    with col3:
        if st.button("🔄 Run Health Check", use_container_width=True):
            st.session_state.strategy_engine.run_health_check()
            st.info("Health check completed!")
    
    with col4:
        if st.button("🚨 Emergency Stop", use_container_width=True, type="primary"):
            st.session_state.strategy_engine.stop()
            st.session_state.strategy_engine.health_monitor.health_status['emergency_stop'] = True
            st.error("🚨 EMERGENCY STOP ACTIVATED")


def main():
    """Main dashboard function."""
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;'>
                <h2 style='color: white; margin: 0;'>🤖 CryptoBots</h2>
                <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>V3.0</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "⚙️ Configuration", "📈 Performance", "🏥 Health Monitor"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Main content
    if page == "📊 Dashboard":
        render_health_status()
        st.markdown("---")
        render_performance_summary()
        st.markdown("---")
        render_active_bots_panel(st.session_state.bot_manager)
        st.markdown("---")
        render_trade_feed(st.session_state.trade_manager, st.session_state.bot_manager)
        st.markdown("---")
        render_bot_controls()
    
    elif page == "⚙️ Configuration":
        render_strategy_config()
    
    elif page == "📈 Performance":
        st.subheader("📈 Performance Analytics")
        st.info("Performance charts coming soon!")
    
    elif page == "🏥 Health Monitor":
        st.subheader("🏥 Health Monitor Details")
        health_data = st.session_state.strategy_engine.health_monitor.health_status
        st.json(health_data)


if __name__ == "__main__":
    main()
