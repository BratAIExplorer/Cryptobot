#!/usr/bin/env python3
"""
Telegram Report Script - Sends trading summary to Telegram
Can be run manually or via cron job for scheduled reports
"""
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def send_telegram_message(token, chat_id, message):
    """Send message via Telegram Bot API"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return None

def get_trading_summary(hours=4):
    """Get trading summary for the last N hours"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'trades.db')
    
    if not os.path.exists(db_path):
        return None
        
    conn = sqlite3.connect(db_path)
    
    # Calculate time threshold
    time_threshold = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Get trades in last N hours
    query = f"""
        SELECT strategy, symbol, side, price, timestamp, amount
        FROM trades 
        WHERE timestamp >= '{time_threshold}'
        ORDER BY timestamp DESC
    """
    
    trades_df = pd.read_sql_query(query, conn)
    
    # Get open positions
    positions_query = """
        SELECT strategy, symbol, entry_price, current_price, 
               (current_price - entry_price) / entry_price * 100 as pnl_pct
        FROM positions 
        WHERE status = 'OPEN'
    """
    
    positions_df = pd.read_sql_query(positions_query, conn)
    
    # Get all-time stats
    all_trades_query = "SELECT COUNT(*) as total, SUM(amount) as volume FROM trades"
    all_stats = pd.read_sql_query(all_trades_query, conn).iloc[0]
    
    conn.close()
    
    return {
        'recent_trades': trades_df,
        'open_positions': positions_df,
        'total_trades': int(all_stats['total']),
        'total_volume': float(all_stats['volume']) if all_stats['volume'] else 0
    }

def format_report(summary, hours=4):
    """Format the summary into a Telegram message"""
    if not summary:
        return "❌ No database found"
    
    # Header
    msg = f"🤖 <b>Crypto Bot Report ({hours}h)</b>\n"
    msg += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    msg += "=" * 30 + "\n\n"
    
    # Recent trades
    recent = summary['recent_trades']
    if len(recent) > 0:
        msg += f"📊 <b>Recent Trades: {len(recent)}</b>\n"
        for _, trade in recent.head(5).iterrows():
            emoji = "🟢" if trade['side'] == 'BUY' else "🔴"
            msg += f"{emoji} {trade['strategy'][:15]}\n"
            msg += f"   {trade['symbol']} @ ${trade['price']:.2f}\n"
        if len(recent) > 5:
            msg += f"   ... and {len(recent) - 5} more\n"
    else:
        msg += f"📊 <b>Recent Trades: 0</b>\n"
        msg += "   No new trades in the last 4 hours\n"
    
    msg += "\n"
    
    # Open positions
    positions = summary['open_positions']
    if len(positions) > 0:
        msg += f"💼 <b>Open Positions: {len(positions)}</b>\n"
        total_pnl = 0
        for _, pos in positions.iterrows():
            pnl = pos['pnl_pct']
            total_pnl += pnl
            emoji = "🟢" if pnl > 0 else "🔴"
            msg += f"{emoji} {pos['symbol']}: {pnl:+.2f}%\n"
        
        avg_pnl = total_pnl / len(positions)
        msg += f"\n📈 <b>Avg P&L: {avg_pnl:+.2f}%</b>\n"
    else:
        msg += f"💼 <b>Open Positions: 0</b>\n"
    
    msg += "\n"
    
    # All-time stats
    msg += f"📊 <b>All-Time Stats</b>\n"
    msg += f"   Total Trades: {summary['total_trades']}\n"
    msg += f"   Total Volume: ${summary['total_volume']:.2f}\n"
    
    return msg

def main():
    # Load config from environment
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        sys.exit(1)
    
    # Get summary
    print("📊 Generating trading summary...")
    summary = get_trading_summary(hours=4)
    
    # Format message
    message = format_report(summary, hours=4)
    
    # Send to Telegram
    print("📤 Sending to Telegram...")
    result = send_telegram_message(token, chat_id, message)
    
    if result and result.get('ok'):
        print("✅ Report sent successfully!")
    else:
        print(f"❌ Failed to send report: {result}")

if __name__ == "__main__":
    main()
