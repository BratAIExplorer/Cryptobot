"""
Watchlist Tracker - Pillar C: Phase 2
Automates daily performance tracking and rejection of failing coins.
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict
from core.database import NewCoinWatchlist
from sqlalchemy import or_

class WatchlistTracker:
    def __init__(self, exchange, logger, notifier):
        self.exchange = exchange
        self.logger = logger
        self.notifier = notifier

    def update_watchlist_performance(self):
        """Perform daily update on all monitored coins."""
        session = self.logger.db.get_session()
        try:
            # Fetch all coins currently being monitored
            monitored_coins = session.query(NewCoinWatchlist).filter(
                NewCoinWatchlist.status == 'MONITORING'
            ).all()

            print(f"📊 [TRACKER] Updating performance for {len(monitored_coins)} coins...")

            for coin in monitored_coins:
                self._update_coin_stats(coin, session)

            session.commit()
        except Exception as e:
            print(f"❌ [TRACKER] Update failed: {e}")
            session.rollback()
        finally:
            session.close()

    def _update_coin_stats(self, coin, session):
        """Update individual coin stats and check for rejection."""
        try:
            # 1. Fetch current market data
            ticker = self.exchange.fetch_ticker(coin.symbol)
            current_price = ticker.get('last', 0)
            current_vol = ticker.get('quoteVolume', 0)

            if current_price == 0:
                return

            # 2. Update Drawdown & Pump metrics
            drawdown = (coin.initial_price - current_price) / coin.initial_price if coin.initial_price > 0 else 0
            pump = (current_price - coin.initial_price) / coin.initial_price if coin.initial_price > 0 else 0

            coin.max_drawdown_pct = max(coin.max_drawdown_pct or 0, drawdown)
            coin.max_pump_pct = max(coin.max_pump_pct or 0, pump)

            # 3. Check for Auto-Rejection Rules
            days_monitored = (datetime.utcnow() - coin.detected_at).days
            
            # Rule 1: Pump & Dump Check (>70% drop from initial)
            if drawdown > 0.70:
                self._reject_coin(coin, "Pump & Dump detected (>70% drawdown from initial)")
                return

            # Rule 2: Volume Collapse (If monitored for >3 days and vol < 10% of initial)
            if days_monitored >= 3 and current_vol < (coin.initial_volume_24h * 0.10):
                self._reject_coin(coin, "Volume collapse (<10% of listing volume)")
                return

            # 4. Record Checkpoints (7, 14, 30 days)
            if days_monitored >= 30 and not coin.day_30_price:
                coin.day_30_price = current_price
                coin.day_30_volume = current_vol
                self._promote_to_review(coin)
            elif days_monitored >= 14 and not coin.day_14_price:
                coin.day_14_price = current_price
                coin.day_14_volume = current_vol
            elif days_monitored >= 7 and not coin.day_7_price:
                coin.day_7_price = current_price
                coin.day_7_volume = current_vol

            coin.updated_at = datetime.utcnow()
            print(f"✅ [TRACKER] Updated {coin.symbol}: Price ${current_price:.4f}, Vol ${current_vol:,.0f}")

        except Exception as e:
            print(f"⚠️ [TRACKER] Failed to update {coin.symbol}: {e}")

    def _reject_coin(self, coin, reason):
        """Mark coin as rejected and notify."""
        coin.status = 'REJECTED'
        coin.rejection_reason = reason
        print(f"❌ [TRACKER] REJECTED {coin.symbol}: {reason}")
        if self.notifier:
            self.notifier.notify_watchlist_rejection(coin.symbol, reason)

    def _promote_to_review(self, coin):
        """Move coin to Manual Review stage."""
        coin.status = 'MANUAL_REVIEW'
        print(f"📋 [TRACKER] PROMOTED {coin.symbol} to Manual Review")
        
        # Prepare a quick performance summary for the alert
        perf = (coin.day_30_price - coin.initial_price) / coin.initial_price if coin.initial_price > 0 else 0
        summary = (
            f"📈 30-Day Growth: {perf:+.2f}%\n"
            f"📉 Max Drawdown: {coin.max_drawdown_pct:.2f}%\n"
            f"📊 Final Price: ${coin.day_30_price:.4f}"
        )
        
        if self.notifier:
            self.notifier.notify_manual_review_required(coin.symbol, coin.coin_type, summary)

if __name__ == "__main__":
    # Test script for manual run
    from core.exchange_unified import UnifiedExchange
    from core.logger import TradeLogger
    from core.notifier import TelegramNotifier
    import sys
    
    # Optional: Mock dependencies for testing
    exchange = UnifiedExchange()
    logger = TradeLogger()
    notifier = TelegramNotifier() # Will only send if config is present
    
    tracker = WatchlistTracker(exchange, logger, notifier)
    tracker.update_watchlist_performance()
