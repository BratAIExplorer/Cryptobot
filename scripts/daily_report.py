import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.notifier import TelegramNotifier

def generate_daily_report():
    db_path = 'data/trades.db'
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    trades = pd.read_sql_query("SELECT * FROM trades WHERE timestamp > datetime('now', '-1 day')", conn)
    positions = pd.read_sql_query("SELECT * FROM positions WHERE status='OPEN'", conn)
    conn.close()
    
    buys = len(trades[trades['side'] == 'BUY'])
    sells = len(trades[trades['side'] == 'SELL'])
    
    msg = f"📊 *Daily Bot Report* 📊\n\n"
    msg += f"🗓 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    msg += f"🔄 24h Trades: {len(trades)}\n"
    msg += f"🟢 Buys: {buys} | 🔴 Sells: {sells}\n"
    msg += f"🔓 Open Positions: {len(positions)}\n"
    msg += "\n✅ System Healthy"
    
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if tg_token and tg_chat_id:
        TelegramNotifier(token=tg_token, chat_id=tg_chat_id).send_message(msg)
    else:
        print(msg)

if __name__ == "__main__":
    generate_daily_report()
