#!/usr/bin/env python3
"""
Position Sell Target Diagnostic
Shows when each position will sell based on grid parameters
"""
import sqlite3
import os
from datetime import datetime

# Auto-detect database path
def find_database():
    """Find the trading database"""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'data', 'multi', 'trades_paper.db'),
        os.path.join(os.path.dirname(__file__), 'data', 'trades_v3_paper.db'),
        os.path.join(os.path.dirname(__file__), 'data', 'trades_paper.db'),
        os.path.join(os.path.dirname(__file__), 'trades_paper.db'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

DB_PATH = find_database()

# Current Grid Parameters (from run_bot.py)
GRID_CONFIGS = {
    'Grid Bot BTC': {
        'lower': 90000,
        'upper': 100000,
        'levels': 40,
        'limit_step_pct': 0.95
    },
    'Grid Bot ETH': {
        'lower': 2800,
        'upper': 4200,
        'levels': 30,
        'limit_step_pct': 0.95
    }
}

def calculate_grid_step(lower, upper, levels):
    """Calculate grid step size"""
    return (upper - lower) / (levels - 1)

def main():
    print("=" * 100)
    print("🔍 POSITION SELL TARGET ANALYSIS")
    print("=" * 100)
    print()

    if not DB_PATH or not os.path.exists(DB_PATH):
        print(f"❌ Database not found!")
        print("\nSearched in:")
        print("  • data/multi/trades_paper.db")
        print("  • data/trades_v3_paper.db")
        print("  • data/trades_paper.db")
        print("\n⚠️  This script must be run on the VPS where the bot is running!")
        return

    print(f"✅ Found database: {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get column names
    cursor.execute("PRAGMA table_info(positions)")
    columns = {col[1]: col[0] for col in cursor.fetchall()}

    # Determine which columns exist
    price_col = 'buy_price' if 'buy_price' in columns else 'price'
    time_col = 'buy_timestamp' if 'buy_timestamp' in columns else 'timestamp'

    # Query open positions
    query = f"""
        SELECT id, strategy, symbol, amount, {price_col} as entry_price, {time_col} as entry_time
        FROM positions
        WHERE status = 'OPEN'
        ORDER BY {time_col} DESC
    """

    cursor.execute(query)
    positions = cursor.fetchall()
    conn.close()

    if not positions:
        print("✅ No open positions found - bot is clean slate!")
        return

    print("=" * 100)
    print("🔍 POSITION SELL TARGET ANALYSIS")
    print("=" * 100)
    print()

    for pos in positions:
        pos_id, strategy, symbol, amount, entry_price, entry_time = pos

        if strategy not in GRID_CONFIGS:
            print(f"⚠️  Position #{pos_id} - {strategy} (no grid config found)")
            continue

        config = GRID_CONFIGS[strategy]
        grid_step = calculate_grid_step(config['lower'], config['upper'], config['levels'])
        sell_target = entry_price + (grid_step * config['limit_step_pct'])

        entry_dt = datetime.fromisoformat(entry_time) if isinstance(entry_time, str) else datetime.fromtimestamp(entry_time)
        age = datetime.now() - entry_dt

        print(f"📊 Position #{pos_id} - {strategy}")
        print(f"   Symbol:        {symbol}")
        print(f"   Entry Price:   ${entry_price:,.2f}")
        print(f"   Grid Step:     ${grid_step:,.2f}")
        print(f"   Sell Target:   ${sell_target:,.2f}")
        print(f"   Price Needed:  +${sell_target - entry_price:,.2f} ({((sell_target / entry_price - 1) * 100):.2f}%)")
        print(f"   Position Age:  {age.days}d {age.seconds // 3600}h")
        print()

    print("=" * 100)
    print("💡 RECOMMENDATIONS")
    print("=" * 100)
    print()
    print("If positions were opened BEFORE parameter changes:")
    print("  • They're using OLD grid step ($1,315 for BTC)")
    print("  • They'll never sell with current prices")
    print()
    print("Solutions:")
    print("  1. CLOSE POSITIONS MANUALLY - Force close stuck positions")
    print("  2. ADJUST GRID PARAMETERS - Widen range temporarily to include old positions")
    print("  3. WAIT FOR BIG MOVE - Wait for price to move enough to trigger old sell targets")
    print()
    print("Recommended: Option 1 (Clean slate with new optimized parameters)")
    print()

if __name__ == "__main__":
    main()
