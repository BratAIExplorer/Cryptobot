#!/usr/bin/env python3
"""
Force Close Stuck Positions
Manually closes positions that are stuck with old grid parameters
"""
import sqlite3
import os
import sys
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

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

def get_open_positions():
    """Get all open positions"""
    if not DB_PATH or not os.path.exists(DB_PATH):
        print(f"❌ Database not found!")
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get column names
    cursor.execute("PRAGMA table_info(positions)")
    columns = {col[1]: col[0] for col in cursor.fetchall()}

    # Determine which columns exist (support multiple schema versions)
    if 'entry_price' in columns:
        price_col = 'entry_price'
    elif 'buy_price' in columns:
        price_col = 'buy_price'
    else:
        price_col = 'price'

    if 'entry_date' in columns:
        time_col = 'entry_date'
    elif 'buy_timestamp' in columns:
        time_col = 'buy_timestamp'
    else:
        time_col = 'timestamp'

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

    return positions

def close_position(position_id, close_price, reason="Manual close - stuck position"):
    """Manually close a position by updating database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get column names
    cursor.execute("PRAGMA table_info(positions)")
    columns = {col[1]: col[0] for col in cursor.fetchall()}

    # Determine entry price column
    if 'entry_price' in columns:
        price_col = 'entry_price'
    elif 'buy_price' in columns:
        price_col = 'buy_price'
    else:
        price_col = 'price'

    # Just mark as CLOSED - this schema doesn't have sell_price/sell_timestamp
    query = """
        UPDATE positions
        SET status = 'CLOSED',
            updated_at = ?
        WHERE id = ?
    """
    cursor.execute(query, (datetime.now().isoformat(), position_id))
    conn.commit()

    # Calculate P&L
    cursor.execute(f"SELECT amount, {price_col} FROM positions WHERE id = ?", (position_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        amount, entry_price = result
        pnl = (close_price - entry_price) * amount
        return pnl
    return 0

def main():
    print("=" * 100)
    print("⚠️  FORCE CLOSE STUCK POSITIONS")
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

    positions = get_open_positions()

    if not positions:
        print("✅ No open positions found!")
        return

    print(f"Found {len(positions)} open position(s):\n")

    # Import exchange adapter to get current prices
    try:
        from adapters.binance_adapter import BinanceAdapter
        exchange = BinanceAdapter(mode='paper')
        print("✅ Connected to exchange for current prices\n")
    except Exception as e:
        print(f"⚠️  Could not connect to exchange: {e}")
        print("⚠️  Will need manual price input\n")
        exchange = None

    total_pnl = 0

    for pos_id, strategy, symbol, amount, entry_price, entry_time in positions:
        entry_dt = datetime.fromisoformat(entry_time) if isinstance(entry_time, str) else datetime.fromtimestamp(entry_time)
        age = datetime.now() - entry_dt

        print(f"📊 Position #{pos_id}")
        print(f"   Strategy:      {strategy}")
        print(f"   Symbol:        {symbol}")
        print(f"   Entry Price:   ${entry_price:,.2f}")
        print(f"   Amount:        {amount}")
        print(f"   Age:           {age.days}d {age.seconds // 3600}h")

        # Get current price
        current_price = None
        if exchange:
            try:
                df = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=1)
                if not df.empty:
                    current_price = float(df['close'].iloc[-1])
                    print(f"   Current Price: ${current_price:,.2f}")
            except Exception as e:
                print(f"   ⚠️  Could not fetch price: {e}")

        if not current_price:
            current_price = float(input(f"   Enter current price for {symbol}: $"))

        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        pnl_usd = (current_price - entry_price) * amount

        print(f"   Unrealized P&L: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
        print()

        # Ask for confirmation
        response = input(f"   Close this position at ${current_price:,.2f}? (y/N): ").strip().lower()

        if response == 'y':
            pnl = close_position(pos_id, current_price)
            total_pnl += pnl
            print(f"   ✅ Position #{pos_id} closed - P&L: ${pnl:+.2f}")
        else:
            print(f"   ⏭️  Skipped position #{pos_id}")

        print()

    print("=" * 100)
    print(f"✅ Complete - Total P&L from closed positions: ${total_pnl:+.2f}")
    print("=" * 100)
    print()
    print("💡 Next steps:")
    print("   1. Restart bot with: bash restart_bot.sh")
    print("   2. New positions will use optimized grid parameters")
    print("   3. Monitor with: tail -f bot.log")
    print()

if __name__ == "__main__":
    main()
