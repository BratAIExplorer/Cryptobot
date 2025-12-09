from decimal import Decimal
import pandas as pd
from datetime import datetime, timedelta
from .database import VetoEvent, Database
from utils.indicators import calculate_atr, calculate_sma

class VetoManager:
    """
    The 'No' Man.
    Authoritative source on whether the bot is ALLOWED to buy.
    """
    def __init__(self, exchange_interface, db_logger=None):
        self.exchange = exchange_interface
        self.logger = db_logger
        self.active_vetoes = [] # List of active VetoEvent objects (in-memory cache)
        self.last_check = datetime.min
        self.cache_duration = 300 # 5 minutes cache for macro checks (BTC status)
        
        # Thresholds
        self.BTC_CRASH_DROP_PCT = 0.05 # 5% drop in 24h triggers crash alert
        self.BTC_DUMP_PCT = 0.03 # 3% drop in 4h triggers dump alert
        
    def check_entry_allowed(self, symbol, strategy_name):
        """
        Master check: Can we enter a trade for this symbol?
        Returns: (bool, reason)
        """
        # 1. Global Market Checks (BTC Status)
        # We check this periodically, not on every tick to save API calls
        if (datetime.now() - self.last_check).total_seconds() > self.cache_duration:
            self._update_global_vetoes()
            self.last_check = datetime.now()
            
        # Check if any GLOBAL vetoes are active
        for veto in self.active_vetoes:
            # Check overlap if veto is specific to coins (future feature), assuming global for now
            return False, f"VETO ACTIVE: {veto.rule_type} - {veto.reason}"
            
        # 2. Local/Specific Checks (Falling Knife on specific symbol)
        is_safe, reason = self._check_falling_knife(symbol)
        if not is_safe:
            return False, reason
            
        return True, "Safe to trade"

    def _update_global_vetoes(self):
        """Update the list of global vetoes (BTC Crash, etc.)"""
        self.active_vetoes = [] # Reset
        
        # A. BTC Crash Check
        is_crash, reason = self._check_btc_crash()
        if is_crash:
            veto = VetoEvent(
                rule_type="BTC_CRASH",
                severity_level=3,
                reason=reason,
                triggered_at=datetime.utcnow()
            )
            self.active_vetoes.append(veto)
            # Log to DB if we can (optional for now)
            if self.logger:
                pass # self.logger.log_veto(veto) OR similar

        # B. Bad News Check (Placeholder for News API)
        # is_bad_news, news_reason = self._check_news_sentiment()
        # if is_bad_news: ...

    def _check_btc_crash(self):
        """
        Analyze BTC to detect market crashes.
        Rule: 
        1. BTC price < SMA 50 (Downtrend) AND
        2. Daily Drop > 5% OR 4h Drop > 3%
        """
        try:
            # Fetch BTC/USDT data
            # using 'Binance' mode implicit in exchange interface usually
            symbol = "BTC/USDT"
            
            # 1. Trend Check (Daily)
            df_daily = self.exchange.fetch_ohlcv(symbol, timeframe='1d', limit=55)
            if df_daily.empty: 
                return False, "No Data"
                
            current_price = df_daily['close'].iloc[-1]
            sma_50 = calculate_sma(df_daily['close'], period=50).iloc[-1]
            
            # Daily % change
            daily_open = df_daily['open'].iloc[-1]
            daily_drop = (current_price - daily_open) / daily_open
            
            # 2. Momentum Check (4h)
            df_4h = self.exchange.fetch_ohlcv(symbol, timeframe='4h', limit=5)
            if not df_4h.empty:
                open_4h = df_4h['open'].iloc[-1]
                drop_4h = (current_price - open_4h) / open_4h
            else:
                drop_4h = 0.0

            # Logic:
            # Hard Veto: Daily drop > 5%
            if daily_drop < -self.BTC_CRASH_DROP_PCT:
                return True, f"BTC Crash detected: Daily drop {daily_drop*100:.1f}%"
            
            # Trend Veto: Below SMA50 AND dropping fast (>3% in 4h)
            if current_price < sma_50 and drop_4h < -self.BTC_DUMP_PCT:
                return True, f"BTC Downtrend & Dump: Below SMA50 & 4h drop {drop_4h*100:.1f}%"

            return False, None
            
        except Exception as e:
            print(f"[VETO] Error checking BTC status: {e}")
            return False, f"Error: {e}"

    def _check_falling_knife(self, symbol):
        """
        Check if the specific symbol is crashing too hard to catch.
        Rule:
        1. Spread is too high (Liquidity dry up)
        2. Recent candle is a massive red candle (>3x ATR)
        """
        try:
            # 1. Spread Check (requires Order Book, but we use ticker for speed if available)
            # For now, we rely on OHLCV volatility analysis as proxy
            
            df = self.exchange.fetch_ohlcv(symbol, timeframe='15m', limit=20)
            if df.empty: return True, "No Data"
            
            # Calculate ATR
            df['atr'] = calculate_atr(df['high'], df['low'], df['close'], period=14)
            current_atr = df['atr'].iloc[-1]
            
            current_open = df['open'].iloc[-1]
            current_close = df['close'].iloc[-1]
            candle_size = abs(current_close - current_open)
            
            # If current candle is huge red candle (> 3x ATR)
            if current_close < current_open and candle_size > (3 * current_atr) and current_atr > 0:
                drop_pct = (current_close - current_open) / current_open
                return False, f"Falling Knife: Large 15m drop {drop_pct*100:.1f}% (>3x ATR)"
                
            return True, "Safe"
            
        except Exception as e:
            # Fail Open (Allow trade if check fails, but log warning)
            print(f"[VETO] Warn: Falling knife check failed for {symbol}: {e}")
            return True, "Check Failed (Fail Open)"
