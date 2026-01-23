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
        Calculate portfolio summary from trade data

        Returns:
            Dictionary with portfolio metrics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total trades
        cursor.execute("SELECT COUNT(*) FROM trades")
        total_trades = cursor.fetchone()[0]

        # Total P&L from positions table (not trades)
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
        total_positions = row[1] or 1  # Avoid division by zero
        win_rate = (wins / total_positions * 100) if total_positions > 0 else 0.0

        # Active positions count
        cursor.execute("SELECT COUNT(*) FROM positions")
        active_positions = cursor.fetchone()[0]

        # Strategy breakdown from bot_status (show ALL active bots)
        # LEFT JOIN with positions to include bots without trades
        cursor.execute("""
            SELECT
                bs.strategy,
                bs.wallet_balance,
                COALESCE(COUNT(p.id), 0) as position_count,
                COALESCE(SUM(p.unrealized_pnl_usd), 0) as strategy_pnl
            FROM bot_status bs
            LEFT JOIN positions p ON bs.strategy = p.strategy
            WHERE bs.status = 'RUNNING'
            GROUP BY bs.strategy, bs.wallet_balance
        """)
        strategies = []
        for row in cursor.fetchall():
            strategies.append({
                "name": row[0],
                "balance": row[1],
                "trades": row[2],
                "pnl": row[3]
            })

        conn.close()

        # Calculate total portfolio value from bot balances
        total_portfolio_value = sum(strategy['balance'] for strategy in strategies)

        return {
            "total_trades": total_trades,
            "total_pnl": round(total_pnl, 2),
            "total_value_usd": round(total_portfolio_value, 2),
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
        start_date = datetime.utcnow() - timedelta(hours=hours)
        return self.get_trades(start_date=start_date, limit=1000)

    def get_strategy_performance(self) -> List[Dict]:
        """
        Get performance metrics per strategy

        Returns:
            List of strategy performance dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                strategy,
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades,
                SUM(COALESCE(pnl, 0)) as total_pnl,
                AVG(COALESCE(pnl, 0)) as avg_pnl,
                MAX(COALESCE(pnl, 0)) as best_trade,
                MIN(COALESCE(pnl, 0)) as worst_trade
            FROM trades
            GROUP BY strategy
            ORDER BY total_pnl DESC
        """)

        results = []
        for row in cursor.fetchall():
            total_closed = row[1] + row[2]
            win_rate = (row[1] / total_closed * 100) if total_closed > 0 else 0.0

            results.append({
                "strategy": row[0],
                "total_trades": row[1],
                "winning_trades": row[1],
                "losing_trades": row[2],
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
