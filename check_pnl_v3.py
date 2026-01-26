
import sqlite3
import pandas as pd
import os

# Database Path
DB_PATH = 'data/multi/trades_paper.db'

def check_pnl():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "=" * 80)
    print("📊 PORTFOLIO PnL REPORT")
    print("=" * 80)

    # 1. Calculate Realized PnL from TRADES table
    # We sum (Sell Amount * Price) - (Buy Amount * Price) for closed positions
    query_realized = """
    SELECT 
        p.strategy,
        COUNT(DISTINCT p.id) as closed_trades,
        SUM(CASE WHEN t.side = 'SELL' THEN t.cost ELSE -t.cost END) as realized_pnl
    FROM positions p
    JOIN trades t ON p.id = t.position_id
    WHERE p.status = 'CLOSED'
    GROUP BY p.strategy
    """
    try:
        df_realized = pd.read_sql_query(query_realized, conn)
    except Exception as e:
        print(f"⚠️ Error calculating realized PnL: {e}")
        df_realized = pd.DataFrame()

    # 2. Open Positions (Unrealized PnL) - This is on the positions table
    query_open = """
    SELECT 
        strategy,
        COUNT(*) as open_trades,
        SUM(unrealized_pnl_usd) as unrealized_pnl,
        SUM(current_value_usd) as current_equity
    FROM positions 
    WHERE status='OPEN'
    GROUP BY strategy
    """
    try:
        df_open = pd.read_sql_query(query_open, conn)
    except Exception as e:
        print(f"⚠️ Error calculating open PnL: {e}")
        df_open = pd.DataFrame()

    # Merge Stats
    if not df_realized.empty or not df_open.empty:
        # Create master list of strategies
        strategies_realized = df_realized['strategy'].tolist() if not df_realized.empty else []
        strategies_open = df_open['strategy'].tolist() if not df_open.empty else []
        all_strategies = set(strategies_realized + strategies_open)
        
        print(f"{'STRATEGY':<25} | {'CLOSED':<8} | {'OPEN':<6} | {'REALIZED':>10} | {'UNREALIZED':>12} | {'TOTAL PnL':>12}")
        print("-" * 88)
        
        grand_total_realized = 0
        grand_total_unrealized = 0
        
        for strategy in sorted(all_strategies):
            # Get closed stats
            closed_row = df_realized[df_realized['strategy'] == strategy] if not df_realized.empty else pd.DataFrame()
            closed_count = closed_row['closed_trades'].iloc[0] if not closed_row.empty else 0
            realized = closed_row['realized_pnl'].iloc[0] if not closed_row.empty else 0
            # Handle None/NaN
            if pd.isna(realized): realized = 0.0
            
            # Get open stats
            open_row = df_open[df_open['strategy'] == strategy] if not df_open.empty else pd.DataFrame()
            open_count = open_row['open_trades'].iloc[0] if not open_row.empty else 0
            unrealized = open_row['unrealized_pnl'].iloc[0] if not open_row.empty else 0
            # Handle None/NaN
            if pd.isna(unrealized): unrealized = 0.0
            
            total_pnl = realized + unrealized
            
            grand_total_realized += realized
            grand_total_unrealized += unrealized
            
            print(f"{strategy:<25} | {closed_count:<8} | {open_count:<6} | ${realized:>9.2f} | ${unrealized:>11.2f} | ${total_pnl:>11.2f}")
            
        print("-" * 88)
        print(f"{'TOTAL PORTFOLIO':<25} | {'-':<8} | {'-':<6} | ${grand_total_realized:>9.2f} | ${grand_total_unrealized:>11.2f} | ${grand_total_realized + grand_total_unrealized:>11.2f}")

    else:
        print("   No trade data found yet.")

    print("\n" + "=" * 80)
    print("📈 ACTIVE POSITIONS SNAPSHOT (Top 10)")
    print("-" * 80)
    
    query_active = """
    SELECT 
        symbol, 
        strategy, 
        entry_price, 
        current_price, 
        unrealized_pnl_pct, 
        unrealized_pnl_usd 
    FROM positions 
    WHERE status='OPEN' 
    ORDER BY unrealized_pnl_usd DESC 
    LIMIT 10
    """
    try:
        df_active = pd.read_sql_query(query_active, conn)
        
        if not df_active.empty:
            for _, row in df_active.iterrows():
                pnl_pct = row['unrealized_pnl_pct'] * 100 if row['unrealized_pnl_pct'] else 0.0
                print(f"{row['symbol']:<10} {row['strategy']:<20} Entry: ${row['entry_price']:<8.4f} Curr: ${row['current_price']:<8.4f} PnL: {pnl_pct:>6.2f}% (${row['unrealized_pnl_usd']:>6.2f})")
        else:
            print("   No active positions.")
    except Exception as e:
        print(f"⚠️ Error reading active positions: {e}")

    print("\n" + "=" * 80)
    conn.close()

if __name__ == "__main__":
    check_pnl()
