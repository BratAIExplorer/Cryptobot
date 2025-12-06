import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = 'data/trades.db'

def health_check():
    """Quick health check to spot obvious issues"""
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*60)
    print("🏥 CRYPTO BOT HEALTH CHECK")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Circuit Breaker Status
    try:
        cb_status = pd.read_sql_query("SELECT * FROM circuit_breaker WHERE id=1", conn).iloc[0]
        if cb_status['is_open']:
            print("❌ CIRCUIT BREAKER: OPEN (Bot is paused!)")
            print(f"   Consecutive Errors: {cb_status['consecutive_errors']}")
            print(f"   Last Error: {cb_status['last_error_time']}")
        else:
            print("✅ CIRCUIT BREAKER: Closed (Normal operation)")
    except:
        print("⚠️  CIRCUIT BREAKER: Unable to check")
    
    # 2. Recent Activity (Last 1 Hour)
    cutoff_1h = datetime.now() - timedelta(hours=1)
    trades_1h = pd.read_sql_query(f"SELECT * FROM trades WHERE timestamp > '{cutoff_1h}'", conn)
    
    if len(trades_1h) == 0:
        print("⚠️  ACTIVITY (1h): No trades in last hour")
    else:
        buys = len(trades_1h[trades_1h['side'] == 'BUY'])
        sells = len(trades_1h[trades_1h['side'] == 'SELL'])
        print(f"✅ ACTIVITY (1h): {len(trades_1h)} trades ({buys} BUY, {sells} SELL)")
    
    # 3. Open Positions Count
    open_pos = pd.read_sql_query("SELECT * FROM positions WHERE status='OPEN'", conn)
    print(f"📊 OPEN POSITIONS: {len(open_pos)}")
    
    if len(open_pos) > 20:
        print("   ⚠️  Warning: High number of open positions (possible accumulation)")
    
    # 4. Strategy Breakdown (Last 24h)
    cutoff_24h = datetime.now() - timedelta(hours=24)
    trades_24h = pd.read_sql_query(f"SELECT * FROM trades WHERE timestamp > '{cutoff_24h}'", conn)
    
    if not trades_24h.empty:
        print("\n📈 STRATEGY ACTIVITY (Last 24h):")
        strategy_counts = trades_24h['strategy'].value_counts()
        for strategy, count in strategy_counts.items():
            print(f"   {strategy}: {count} trades")
    else:
        print("\n⚠️  No trades in last 24 hours")
    
    # 5. Stuck Position Check
    if not open_pos.empty:
        open_pos['buy_timestamp'] = pd.to_datetime(open_pos['buy_timestamp'])
        open_pos['age_hours'] = (datetime.now() - open_pos['buy_timestamp']).dt.total_seconds() / 3600
        
        very_old = open_pos[open_pos['age_hours'] > 48]
        if not very_old.empty:
            print(f"\n⚠️  STUCK POSITIONS: {len(very_old)} positions older than 48h")
            for _, pos in very_old.iterrows():
                print(f"   Position #{pos['id']}: {pos['symbol']} ({pos['age_hours']:.1f}h old)")
    
    # 6. Quick P&L Summary
    all_closed = pd.read_sql_query("SELECT profit FROM positions WHERE status='CLOSED'", conn)
    if not all_closed.empty:
        total_pnl = all_closed['profit'].sum()
        print(f"\n💰 TOTAL P&L: ${total_pnl:.2f}")
    
    print("\n" + "="*60)
    print("TIP: Run this every 2-4 hours to monitor bot health")
    print("="*60 + "\n")
    
    conn.close()

if __name__ == "__main__":
    health_check()
