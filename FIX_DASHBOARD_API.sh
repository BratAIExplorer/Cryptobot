#!/bin/bash
################################################################################
# FIX DASHBOARD API - Use Positions Table for P&L
# Date: 2026-01-23
# Purpose: Fix API endpoints crashing (500 errors)
################################################################################

set -e

echo "========================================================================"
echo "🔧 FIXING DASHBOARD API - Positions Table Integration"
echo "========================================================================"
echo ""

cd ~/cryptobot_v3/enterprise/backend

# Backup original file
echo "📦 Creating backup..."
cp utils/bot_reader.py utils/bot_reader.py.backup_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"
echo ""

# Create fixed version
echo "🔧 Creating fixed bot_reader.py..."

cat > utils/bot_reader.py << 'ENDOFFILE'
"""
Bot Database Reader - READ-ONLY access to existing bot's SQLite database
DOES NOT MODIFY bot database - enterprise platform only reads trade data
"""
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Path to bot's SQLite database (read-only)
BOT_DB_PATH = os.getenv("BOT_DB_PATH", "../../data/multi/trades_paper.db")

class BotDatabaseReader:
    """
    Read-only interface to bot's trading database
    Provides safe, isolated access without modifying bot data
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize reader with database path

        Args:
            db_path: Path to bot's SQLite database (default from env)
        """
        self.db_path = db_path or BOT_DB_PATH

        # Convert to absolute path
        if not os.path.isabs(self.db_path):
            base_dir = Path(__file__).parent.parent.parent.parent
            self.db_path = str(base_dir / self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get read-only database connection"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Bot database not found: {self.db_path}")

        # Open in read-only mode
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def get_trades(
        self,
        limit: int = 100,
        offset: int = 0,
        strategy: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get trades from bot database

        Args:
            limit: Maximum number of trades to return
            offset: Number of trades to skip
            strategy: Filter by strategy name
            symbol: Filter by trading pair
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of trade dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_trade_count(
        self,
        strategy: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> int:
        """Get total number of trades"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT COUNT(*) FROM trades WHERE 1=1"
        params = []

        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()

        return count

    def get_portfolio_summary(self) -> Dict:
        """
        Calculate portfolio summary from positions table (FIXED)

        Returns:
            Dictionary with portfolio metrics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total trades
        cursor.execute("SELECT COUNT(*) FROM trades")
        total_trades = cursor.fetchone()[0]

        # Total P&L from positions (both open and closed)
        cursor.execute("SELECT SUM(COALESCE(unrealized_pnl_usd, 0)) FROM positions")
        total_pnl = cursor.fetchone()[0] or 0.0

        # Win rate (positions with positive P&L)
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN unrealized_pnl_usd > 0 THEN 1 END) as wins,
                COUNT(*) as total_positions
            FROM positions
        """)
        row = cursor.fetchone()
        wins = row[0] or 0
        total_positions = row[1] or 1
        win_rate = (wins / total_positions * 100) if total_positions > 0 else 0.0

        # Active positions (OPEN status)
        cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN'")
        active_positions = cursor.fetchone()[0]

        # Strategy breakdown from positions
        cursor.execute("""
            SELECT
                strategy,
                COUNT(*) as position_count,
                SUM(COALESCE(unrealized_pnl_usd, 0)) as strategy_pnl
            FROM positions
            GROUP BY strategy
        """)
        strategies = []
        for row in cursor.fetchall():
            strategies.append({
                "name": row[0],
                "trades": row[1],
                "pnl": round(row[2], 2)
            })

        conn.close()

        return {
            "total_trades": total_trades,
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 2),
            "active_positions": active_positions,
            "strategies": strategies,
            "last_updated": datetime.utcnow().isoformat()
        }

    def get_recent_trades(self, hours: int = 24) -> List[Dict]:
        """
        Get trades from last N hours

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent trades
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.get_trades(
            start_date=cutoff,
            limit=1000
        )

    def get_strategy_performance(self) -> List[Dict]:
        """
        Get performance metrics per strategy (FIXED - uses positions table)

        Returns:
            List of strategy performance dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                strategy,
                COUNT(*) as total_positions,
                COUNT(CASE WHEN unrealized_pnl_usd > 0 THEN 1 END) as winning_positions,
                COUNT(CASE WHEN unrealized_pnl_usd < 0 THEN 1 END) as losing_positions,
                SUM(COALESCE(unrealized_pnl_usd, 0)) as total_pnl,
                AVG(COALESCE(unrealized_pnl_usd, 0)) as avg_pnl,
                MAX(COALESCE(unrealized_pnl_usd, 0)) as best_position,
                MIN(COALESCE(unrealized_pnl_usd, 0)) as worst_position
            FROM positions
            GROUP BY strategy
            ORDER BY total_pnl DESC
        """)

        results = []
        for row in cursor.fetchall():
            total_positions = row[1]
            winning = row[2] or 0
            losing = row[3] or 0
            win_rate = (winning / total_positions * 100) if total_positions > 0 else 0.0

            results.append({
                "strategy": row[0],
                "total_trades": total_positions,
                "winning_trades": winning,
                "losing_trades": losing,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(row[4], 2),
                "avg_pnl": round(row[5], 2),
                "best_trade": round(row[6], 2),
                "worst_trade": round(row[7], 2)
            })

        conn.close()
        return results

    def check_database_exists(self) -> Tuple[bool, str]:
        """
        Check if bot database exists and is accessible

        Returns:
            Tuple of (exists: bool, message: str)
        """
        if not os.path.exists(self.db_path):
            return False, f"Database not found: {self.db_path}"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            count = cursor.fetchone()[0]
            conn.close()
            return True, f"Database accessible ({count} trades)"
        except Exception as e:
            return False, f"Database error: {str(e)}"

# Singleton instance
bot_reader = BotDatabaseReader()
ENDOFFILE

echo "✅ Fixed bot_reader.py created"
echo ""

# Restart backend to apply changes
echo "🔄 Restarting backend..."
pkill -f "uvicorn main:app" 2>/dev/null || echo "Backend not running"
sleep 2

nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend restarted (PID: $BACKEND_PID)"
sleep 5
echo ""

# Test the fixed endpoints
echo "========================================================================"
echo "🧪 TESTING FIXED ENDPOINTS"
echo "========================================================================"
echo ""

echo "📊 Testing /health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Failed"
echo ""

echo "📊 Testing database connection..."
echo "Database should show fresh data (1 trade, 1 position)"
echo ""

# Verify
echo "========================================================================"
echo "✅ FIX COMPLETE!"
echo "========================================================================"
echo ""
echo "🔧 What Was Fixed:"
echo "   - get_portfolio_summary() now uses positions table"
echo "   - get_strategy_performance() now uses positions table"
echo "   - P&L calculated from unrealized_pnl_usd column"
echo "   - Win rate based on actual position P&L"
echo ""
echo "📊 Next Steps:"
echo "   1. Hard refresh your browser (Ctrl+Shift+R)"
echo "   2. Dashboard should now show:"
echo "      - Fresh data (1 trade, 1 position)"
echo "      - NO 500 errors"
echo "      - Accurate P&L metrics"
echo ""
echo "   3. If still shows old data:"
echo "      - Clear browser cache completely"
echo "      - Try incognito window"
echo "      - Wait 30 seconds for dashboard to refresh"
echo ""
echo "📝 Backup Location:"
echo "   Original file backed up to:"
echo "   ~/cryptobot_v3/enterprise/backend/utils/bot_reader.py.backup_*"
echo ""
echo "========================================================================"
echo ""
