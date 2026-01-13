"""
CryptoBots V3 - Dashboard Panels
Additional panels for active bots, wallet balances, and bot management.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List


def render_trading_mode_selector(testnet_manager) -> str:
    """Render trading mode selector."""
    st.sidebar.markdown("### 🌐 Trading Mode")
    
    mode = st.sidebar.radio(
        "Select Mode",
        options=['paper', 'testnet', 'live'],
        format_func=lambda x: {
            'paper': '📝 Paper Trading (No API)',
            'testnet': '🧪 Binance Testnet (Recommended)',
            'live': '💸 Live Trading (Real Money!)'
        }[x],
        index=1,  # Default to testnet
        key='trading_mode_selector',
        label_visibility="collapsed"
    )
    
    if mode == 'live':
        st.sidebar.warning("⚠️ **LIVE MODE** - Real money at risk!")
    elif mode == 'testnet':
        st.sidebar.info("🧪 Using Binance Testnet (fake money)")
    
    return mode


def render_active_bots_panel(bot_manager):
    """Render active bots status panel."""
    st.subheader("🤖 Active Bots")
    
    bots = bot_manager.get_all_bots()
    
    if not bots:
        st.info("No bots configured. Create a bot to get started!")
        
        if st.button("➕ Create New Bot"):
            st.session_state.show_bot_creator = True
        return
    
    # Create DataFrame for bot display
    bot_data = []
    for bot in bots:
        bot_dict = bot.to_dict()
        bot_data.append({
            'Status': bot.get_status_emoji(),
            'Name': bot.name,
            'Strategy': bot.strategy_type.replace('_', ' ').title(),
            'Pair': bot.symbol,
            'P&L': f"${bot.total_pnl:+.2f}",
            'Trades': bot.total_trades,
            'Win Rate': f"{bot.get_win_rate():.1f}%",
            'Balance': f"${bot.get_available_balance():.2f}",
            'ID': bot.id
        })
    
    df = pd.DataFrame(bot_data)
    
    # Display as interactive table
    for idx, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([0.5, 3, 2, 1])
        
        with col1:
            st.markdown(f"### {row['Status']}")
        
        with col2:
            st.markdown(f"**{row['Name']}**")
            st.caption(f"{row['Strategy']} • {row['Pair']}")
        
        with col3:
            pnl_color = "green" if "+" in row['P&L'] else "red"
            st.markdown(f"<span style='color:{pnl_color}; font-weight:bold'>{row['P&L']}</span>", unsafe_allow_html=True)
            st.caption(f"{row['Trades']} trades • {row['Win Rate']} win rate")
        
        with col4:
            bot = bot_manager.get_bot(row['ID'])
            if bot.status == 'running':
                if st.button("⏸️", key=f"pause_{row['ID']}"):
                    bot_manager.pause_bot(row['ID'])
                    st.rerun()
            else:
                if st.button("▶️", key=f"start_{row['ID']}"):
                    bot_manager.start_bot(row['ID'])
                    st.rerun()
        
        st.markdown("---")


def render_wallet_balance_panel(testnet_manager, trading_mode='testnet'):
    """Render wallet balance display."""
    st.subheader("💼 Wallet Balances")
    
    wallet = testnet_manager.get_wallet_summary(trading_mode)
    
    if 'error' in wallet:
        st.error(f"⚠️ Failed to fetch wallet: {wallet['error']}")
        return
    
    # Total balance card
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Balance",
            f"${wallet['total_usd']:,.2f}",
            delta=None
        )
    
    with col2:
        mode_label = {
            'paper': '📝 Paper',
            'testnet': '🧪 Testnet',
            'live': '💸 Live'
        }.get(trading_mode, trading_mode)
        st.metric("Mode", mode_label)
    
    with col3:
        num_assets = len(wallet.get('balances', {}))
        st.metric("Assets", num_assets)
    
    st.markdown("---")
    
    # Individual balances
    balances = wallet.get('balances', {})
    
    if not balances:
        st.info("No balances found. Fund your account to start trading!")
        return
    
    # Display each currency
    for currency, data in balances.items():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        
        with col1:
            st.markdown(f"**{currency}**")
        
        with col2:
            st.markdown(f"{data['total']:.8f}")
        
        with col3:
            usd_value = data.get('usd_value', 0)
            st.markdown(f"${usd_value:,.2f}")
        
        with col4:
            free_pct = (data['free'] / data['total'] * 100) if data['total'] > 0 else 0
            st.markdown(f"Free: {free_pct:.0f}%")


def render_bot_creator_modal(bot_manager):
    """Render bot creation form."""
    st.subheader("➕ Create New Bot")
    
    with st.form("create_bot_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            bot_name = st.text_input("Bot Name", value="My Trading Bot")
            
            strategy = st.selectbox(
                "Strategy",
                options=['buy_dip', 'take_profit', 'trend_following'],
                format_func=lambda x: {
                    'buy_dip': 'Buy @ DIP',
                    'take_profit': 'Take Profit',
                    'trend_following': 'Trend Following'
                }[x]
            )
        
        with col2:
            symbol = st.selectbox(
                "Trading Pair",
                options=['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'MATIC/USDT']
            )
            
            max_allocation = st.number_input(
                "Max Allocation (USDT)",
                min_value=10.0,
                max_value=10000.0,
                value=100.0,
                step=10.0
            )
        
        submitted = st.form_submit_button("Create Bot")
        
        if submitted:
            # Create bot
            bot_config = {
                'name': bot_name,
                'strategy': strategy,
                'symbol': symbol,
                'max_allocation': max_allocation,
                'enabled': False  # Start disabled
            }
            
            bot = bot_manager.create_bot(bot_config)
            st.success(f"✅ Bot '{bot.name}' created successfully!")
            st.session_state.show_bot_creator = False
            st.rerun()


def render_quick_stats(bot_manager):
    """Render quick statistics."""
    summary = bot_manager.to_dict()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Bots", summary['total_bots'])
    
    with col2:
        st.metric("Running", summary['running_bots'])
    
    with col3:
        total_pnl = summary['total_pnl']
        st.metric("Total P&L", f"${total_pnl:+,.2f}", delta=f"{total_pnl:+.2f}")
    
    with col4:
        st.metric("Win Rate", f"{summary['overall_win_rate']:.1f}%")


def render_trade_feed(trade_manager, bot_manager):
    """Render detailed trade history feed."""
    st.subheader("📜 Trade History & Analysis")
    
    # Filters
    col1, col2 = st.columns([3, 1])
    with col1:
        # Get list of bots for filter
        bots = bot_manager.get_all_bots()
        bot_options = {bot.id: bot.name for bot in bots}
        bot_options['all'] = "All Bots"
        
        selected_bot_id = st.selectbox(
            "Filter by Bot",
            options=['all'] + list(bot_options.keys())[:-1], # Remove 'all' duplicate if any
            format_func=lambda x: bot_options.get(x, x)
        )
    
    with col2:
        limit = st.selectbox("Rows", [10, 20, 50, 100], index=1)
    
    # Get trades
    if selected_bot_id == 'all':
        trades = trade_manager.get_trades(limit=limit)
    else:
        trades = trade_manager.get_trades(bot_id=selected_bot_id, limit=limit)
    
    if not trades:
        st.info("No trades found matching criteria.")
        return
        
    # Render trades
    for trade in trades:
        # Determine color and icon
        is_buy = trade['side'] == 'buy'
        color = "green" if trade['pnl'] >= 0 else "red"
        icon = "🟢" if is_buy else "🔴"
        
        with st.expander(f"{icon} {trade['side'].upper()} {trade['symbol']} @ ${trade['price']:,.2f} ({trade['timestamp'][:16].replace('T', ' ')})"):
            
            # Top Row: Key Stats
            t_col1, t_col2, t_col3, t_col4 = st.columns(4)
            with t_col1:
                st.markdown(f"**Bot:** {trade['bot_name']}")
            with t_col2:
                st.markdown(f"**Amount:** {trade['amount']}")
            with t_col3:
                st.markdown(f"**Value:** ${trade['value']:,.2f}")
            with t_col4:
                if trade.get('pnl'):
                    st.markdown(f"**P&L:** <span style='color:{color}'>${trade['pnl']:+.2f}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("**P&L:** Open")

            st.markdown("---")
            
            # Bottom Row: Deep Dive Details (RSI, Strategy)
            details = trade.get('details', {})
            st.markdown("#### 🔬 Deep Dive Analysis")
            
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.markdown("**Strategy Signals:**")
                st.json({
                    "Strategy": trade['strategy'],
                    "Reason": details.get('reason', 'N/A'),
                    "Trend": details.get('trend', 'Neutral')
                })
            
            with d_col2:
                st.markdown("**Technical Indicators:**")
                # Visual RSI Bar
                rsi = details.get('rsi_14', 50)
                st.markdown(f"**RSI (14):** {rsi}")
                st.progress(min(max(rsi, 0), 100) / 100)
                
                # Other indicators
                extra_indi = {k: v for k, v in details.items() if k not in ['reason', 'trend', 'rsi_14']}
                if extra_indi:
                    st.write(extra_indi)
