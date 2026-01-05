"""
Capital Allocation Controller - Prevents bots from exceeding allocated budgets
CRITICAL for live trading - ensures bots cannot overspend
"""
from datetime import datetime, timedelta
from decimal import Decimal

class CapitalController:
    """
    Enforces strict capital limits per bot and overall portfolio
    Prevents any single bot from exceeding its allocation
    """

    def __init__(self, logger, notifier=None):
        self.logger = logger
        self.notifier = notifier
        self.bot_allocations = {}  # {bot_name: max_amount}
        self.bot_spent = {}  # {bot_name: current_spent}
        self.total_portfolio_limit = 0
        self.total_spent = 0
        self.daily_loss_limit = None
        self.daily_loss_start = datetime.now().date()

    def set_bot_allocation(self, bot_name, max_allocation):
        """
        Set maximum capital allocation for a bot
        Args:
            bot_name: Name of the bot
            max_allocation: Maximum USD the bot can use
        """
        self.bot_allocations[bot_name] = float(max_allocation)
        self.bot_spent[bot_name] = 0.0
        self.total_portfolio_limit += float(max_allocation)
        print(f"[Capital Control] {bot_name}: ${max_allocation:,.2f} allocated")

    def set_daily_loss_limit(self, limit_usd):
        """Set maximum daily loss allowed across all bots"""
        self.daily_loss_limit = float(limit_usd)
        print(f"[Capital Control] Daily loss limit: ${limit_usd:,.2f}")

    def check_trade_allowed(self, bot_name, trade_amount, symbol):
        """
        Check if a trade is within allocation limits
        Returns: (allowed: bool, reason: str)
        """
        trade_amount = float(trade_amount)

        # Check 1: Bot has allocation set
        if bot_name not in self.bot_allocations:
            return False, f"Bot {bot_name} has no allocation set"

        # Check 2: Bot has not exceeded its allocation
        current_spent = self.bot_spent.get(bot_name, 0.0)
        allocation = self.bot_allocations[bot_name]

        if current_spent + trade_amount > allocation:
            excess = (current_spent + trade_amount) - allocation
            if self.notifier:
                self.notifier.alert_capital_limit_reached(
                    bot_name=bot_name,
                    attempted_amount=trade_amount,
                    limit=allocation,
                    reason=f"Would exceed by ${excess:.2f}"
                )
            return False, f"Exceeds allocation (${current_spent:.2f} + ${trade_amount:.2f} > ${allocation:.2f})"

        # Check 3: Daily loss limit (if set)
        if self.daily_loss_limit:
            daily_pnl = self._get_daily_pnl()
            if daily_pnl < -self.daily_loss_limit:
                if self.notifier:
                    self.notifier.alert_daily_loss_limit(daily_pnl, self.daily_loss_limit)
                return False, f"Daily loss limit reached (${daily_pnl:.2f})"

        # Check 4: Total portfolio limit
        if self.total_spent + trade_amount > self.total_portfolio_limit:
            return False, f"Exceeds total portfolio limit (${self.total_portfolio_limit:,.2f})"

        return True, "OK"

    def record_trade(self, bot_name, trade_amount, side):
        """
        Record a trade execution
        Args:
            bot_name: Name of the bot
            trade_amount: USD amount of trade
            side: 'BUY' or 'SELL'
        """
        trade_amount = float(trade_amount)

        if side == 'BUY':
            # Increase spent amount
            self.bot_spent[bot_name] = self.bot_spent.get(bot_name, 0.0) + trade_amount
            self.total_spent += trade_amount
        elif side == 'SELL':
            # Decrease spent amount (free up capital)
            self.bot_spent[bot_name] = max(0, self.bot_spent.get(bot_name, 0.0) - trade_amount)
            self.total_spent = max(0, self.total_spent - trade_amount)

        self._log_status(bot_name)

    def get_available_capital(self, bot_name):
        """Get remaining available capital for a bot"""
        if bot_name not in self.bot_allocations:
            return 0.0

        allocation = self.bot_allocations[bot_name]
        spent = self.bot_spent.get(bot_name, 0.0)
        return max(0, allocation - spent)

    def get_utilization(self, bot_name):
        """Get capital utilization percentage for a bot"""
        if bot_name not in self.bot_allocations:
            return 0.0

        allocation = self.bot_allocations[bot_name]
        if allocation == 0:
            return 0.0

        spent = self.bot_spent.get(bot_name, 0.0)
        return (spent / allocation) * 100

    def _get_daily_pnl(self):
        """Calculate today's P&L from database"""
        try:
            # Reset if new day
            today = datetime.now().date()
            if today != self.daily_loss_start:
                self.daily_loss_start = today

            # Query database for today's closed positions
            query = """
                SELECT SUM(unrealized_pnl_usd) as daily_pnl
                FROM positions
                WHERE status='CLOSED'
                AND DATE(exit_time) = ?
            """
            result = self.logger.db.execute(query, (str(today),)).fetchone()
            return result[0] if result and result[0] else 0.0

        except Exception as e:
            print(f"[Capital Control] Error calculating daily P&L: {e}")
            return 0.0

    def _log_status(self, bot_name):
        """Log current capital status"""
        spent = self.bot_spent.get(bot_name, 0.0)
        allocation = self.bot_allocations.get(bot_name, 0.0)
        available = allocation - spent
        utilization = (spent / allocation * 100) if allocation > 0 else 0

        print(f"[Capital Control] {bot_name}: "
              f"Used ${spent:.2f} / ${allocation:.2f} ({utilization:.1f}%) "
              f"| Available: ${available:.2f}")

    def get_portfolio_summary(self):
        """Get complete portfolio capital status"""
        summary = {
            'total_limit': self.total_portfolio_limit,
            'total_spent': self.total_spent,
            'total_available': self.total_portfolio_limit - self.total_spent,
            'utilization_pct': (self.total_spent / self.total_portfolio_limit * 100)
                               if self.total_portfolio_limit > 0 else 0,
            'bots': []
        }

        for bot_name in self.bot_allocations:
            summary['bots'].append({
                'name': bot_name,
                'allocation': self.bot_allocations[bot_name],
                'spent': self.bot_spent.get(bot_name, 0.0),
                'available': self.get_available_capital(bot_name),
                'utilization_pct': self.get_utilization(bot_name)
            })

        return summary

    def print_summary(self):
        """Print capital allocation summary to console"""
        summary = self.get_portfolio_summary()

        print("\n" + "=" * 60)
        print("💰 CAPITAL ALLOCATION STATUS")
        print("=" * 60)
        print(f"Total Portfolio: ${summary['total_limit']:,.2f}")
        print(f"Currently Used:  ${summary['total_spent']:,.2f} ({summary['utilization_pct']:.1f}%)")
        print(f"Available:       ${summary['total_available']:,.2f}")

        if self.daily_loss_limit:
            daily_pnl = self._get_daily_pnl()
            print(f"Daily P&L:       ${daily_pnl:+,.2f} (Limit: -${self.daily_loss_limit:,.2f})")

        print("\nPer-Bot Allocation:")
        for bot in summary['bots']:
            print(f"  {bot['name']:25s} | "
                  f"${bot['spent']:6,.0f} / ${bot['allocation']:6,.0f} | "
                  f"{bot['utilization_pct']:5.1f}% | "
                  f"Available: ${bot['available']:6,.0f}")

        print("=" * 60 + "\n")

    def enforce_sync_with_database(self):
        """
        Sync capital tracking with actual open positions in database
        Ensures accuracy after bot restart
        """
        try:
            # Query all open positions
            query = """
                SELECT bot_id, SUM(position_size_usd) as total_invested
                FROM positions
                WHERE status='OPEN'
                GROUP BY bot_id
            """
            results = self.logger.db.execute(query).fetchall()

            # Reset spent amounts
            for bot_name in self.bot_spent:
                self.bot_spent[bot_name] = 0.0

            self.total_spent = 0.0

            # Update from database
            for row in results:
                bot_id = row[0]
                invested = float(row[1]) if row[1] else 0.0

                if bot_id in self.bot_spent:
                    self.bot_spent[bot_id] = invested
                    self.total_spent += invested

            print(f"[Capital Control] Synced with database: ${self.total_spent:,.2f} in open positions")

        except Exception as e:
            print(f"[Capital Control] Error syncing with database: {e}")
