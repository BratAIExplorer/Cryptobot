import pandas as pd
import numpy as np

def calculate_sma(series, period):
    """Calculate Simple Moving Average"""
    return series.rolling(window=period).mean()

def calculate_rsi(series, period=14):
    """Calculate Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger_bands(series, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = calculate_sma(series, period)
    std = series.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, lower

def calculate_atr(df, period=14):
    """
    Calculate Average True Range (ATR)

    Args:
        df: DataFrame with 'high', 'low', 'close' columns OR
            high, low, close as separate Series (legacy support)
        period: ATR period (default 14)

    Returns:
        Series with ATR values
    """
    # Handle both DataFrame and individual Series inputs
    if isinstance(df, pd.DataFrame):
        high = df['high']
        low = df['low']
        close = df['close']
    else:
        # Legacy: individual Series passed (high, low, close)
        high = df
        low = period if not isinstance(period, int) else None
        close = None
        period = 14 if isinstance(period, pd.Series) else period

        # This is messy but maintains backward compatibility
        # Better to always use DataFrame going forward

    # TR = Max(High-Low, Abs(High-PrevClose), Abs(Low-PrevClose))
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)

    return true_range.rolling(window=period).mean()


def calculate_adx(df, period=14):
    """
    Calculate Average Directional Index (ADX)

    ADX measures trend strength (not direction):
    - ADX < 20: Weak/no trend (choppy, sideways)
    - ADX 20-25: Emerging trend
    - ADX 25-50: Strong trend
    - ADX 50+: Very strong trend

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ADX period (default 14)

    Returns:
        Series with ADX values
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # Calculate True Range
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    tr = ranges.max(axis=1)

    # Calculate Directional Movement
    plus_dm = high.diff()
    minus_dm = -low.diff()

    # Only keep positive movements
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    # Smooth with Wilder's moving average (exponential)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)

    # Calculate ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()

    return adx


def calculate_macd(series, fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence)

    MACD is a momentum indicator:
    - MACD > Signal: Bullish momentum
    - MACD < Signal: Bearish momentum
    - Crossovers indicate momentum shifts

    Args:
        series: Price series (typically 'close')
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)

    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


# ==================== DIRECTIONAL VOLUME ANALYSIS ====================

def calculate_obv(df):
    """
    Calculate On-Balance Volume (OBV)

    OBV tracks cumulative buying/selling pressure:
    - Rising OBV: Accumulation (buyers in control)
    - Falling OBV: Distribution (sellers in control)
    - OBV divergence from price: Potential reversal signal

    Args:
        df: DataFrame with 'close' and 'volume' columns

    Returns:
        Series with OBV values
    """
    obv = pd.Series(index=df.index, dtype='float64')
    obv.iloc[0] = df['volume'].iloc[0]

    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['close'].iloc[i-1]:
            # Price up: Add volume
            obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
        elif df['close'].iloc[i] < df['close'].iloc[i-1]:
            # Price down: Subtract volume
            obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
        else:
            # Price unchanged: Keep OBV same
            obv.iloc[i] = obv.iloc[i-1]

    return obv


def calculate_volume_ratio(df, period=20):
    """
    Calculate Buy vs Sell Volume Ratio

    Estimates buying/selling pressure based on candle direction:
    - Green candles (close > open): Buy volume
    - Red candles (close < open): Sell volume

    Args:
        df: DataFrame with 'open', 'close', 'volume' columns
        period: Rolling period for ratio calculation

    Returns:
        Dict with:
            'buy_volume': Series of buy volume
            'sell_volume': Series of sell volume
            'buy_sell_ratio': Series of ratio (>1 = buying pressure, <1 = selling pressure)
            'net_volume': Series of net volume (buy - sell)
    """
    # Classify volume as buy or sell based on candle color
    buy_volume = df['volume'].where(df['close'] >= df['open'], 0)
    sell_volume = df['volume'].where(df['close'] < df['open'], 0)

    # Rolling sums
    buy_vol_sum = buy_volume.rolling(window=period).sum()
    sell_vol_sum = sell_volume.rolling(window=period).sum()

    # Buy/Sell ratio (avoid division by zero)
    ratio = buy_vol_sum / sell_vol_sum.replace(0, 1)

    # Net volume (positive = buying, negative = selling)
    net_volume = (buy_vol_sum - sell_vol_sum).rolling(window=5).mean()  # Smoothed

    return {
        'buy_volume': buy_volume,
        'sell_volume': sell_volume,
        'buy_sell_ratio': ratio,
        'net_volume': net_volume
    }


def calculate_accumulation_distribution(df):
    """
    Calculate Accumulation/Distribution Line (A/D Line)

    More sophisticated than OBV - considers where price closed within the range:
    - Close near high: Strong buying (multiplier closer to +1)
    - Close near low: Strong selling (multiplier closer to -1)

    Args:
        df: DataFrame with 'high', 'low', 'close', 'volume' columns

    Returns:
        Series with A/D Line values
    """
    # Money Flow Multiplier
    # ((Close - Low) - (High - Close)) / (High - Low)
    clv = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])

    # Handle division by zero (when high == low)
    clv = clv.replace([np.inf, -np.inf], 0).fillna(0)

    # Money Flow Volume
    mfv = clv * df['volume']

    # Cumulative A/D Line
    ad_line = mfv.cumsum()

    return ad_line


def calculate_vpt(df):
    """
    Calculate Volume Price Trend (VPT)

    Similar to OBV but weighted by percentage price change:
    - More sensitive to price movements than OBV
    - Trend confirmation indicator

    Args:
        df: DataFrame with 'close' and 'volume' columns

    Returns:
        Series with VPT values
    """
    # Calculate percentage price change
    price_change_pct = df['close'].pct_change()

    # VPT = Previous VPT + (Volume * % Price Change)
    vpt = (df['volume'] * price_change_pct).cumsum()

    return vpt


def analyze_volume_pressure(df, lookback=20):
    """
    Comprehensive volume pressure analysis

    Combines multiple volume indicators to determine buying/selling pressure

    Args:
        df: DataFrame with OHLCV data
        lookback: Period for analysis

    Returns:
        Dict with:
            'pressure': str ('STRONG_BUY' | 'BUY' | 'NEUTRAL' | 'SELL' | 'STRONG_SELL')
            'obv_trend': str ('RISING' | 'FALLING' | 'FLAT')
            'buy_sell_ratio': float
            'ad_trend': str ('RISING' | 'FALLING' | 'FLAT')
            'confidence': float (0-100)
    """
    # Calculate all volume indicators
    obv = calculate_obv(df)
    vol_ratio = calculate_volume_ratio(df, period=lookback)
    ad_line = calculate_accumulation_distribution(df)

    # Analyze trends (last N periods)
    obv_recent = obv.iloc[-lookback:]
    ad_recent = ad_line.iloc[-lookback:]

    # OBV trend
    obv_slope = (obv_recent.iloc[-1] - obv_recent.iloc[0]) / obv_recent.iloc[0] if obv_recent.iloc[0] != 0 else 0
    if obv_slope > 0.05:
        obv_trend = 'RISING'
        obv_signal = 1
    elif obv_slope < -0.05:
        obv_trend = 'FALLING'
        obv_signal = -1
    else:
        obv_trend = 'FLAT'
        obv_signal = 0

    # A/D trend
    ad_slope = (ad_recent.iloc[-1] - ad_recent.iloc[0]) / abs(ad_recent.iloc[0]) if ad_recent.iloc[0] != 0 else 0
    if ad_slope > 0.05:
        ad_trend = 'RISING'
        ad_signal = 1
    elif ad_slope < -0.05:
        ad_trend = 'FALLING'
        ad_signal = -1
    else:
        ad_trend = 'FLAT'
        ad_signal = 0

    # Buy/Sell ratio
    current_ratio = vol_ratio['buy_sell_ratio'].iloc[-1]
    if current_ratio > 1.5:
        ratio_signal = 1  # Strong buying
    elif current_ratio > 1.1:
        ratio_signal = 0.5  # Moderate buying
    elif current_ratio < 0.67:
        ratio_signal = -1  # Strong selling
    elif current_ratio < 0.9:
        ratio_signal = -0.5  # Moderate selling
    else:
        ratio_signal = 0  # Neutral

    # Combine signals
    total_signal = obv_signal + ad_signal + ratio_signal
    num_indicators = 3

    # Determine pressure
    if total_signal >= 2:
        pressure = 'STRONG_BUY'
        confidence = min(abs(total_signal) / num_indicators * 100, 100)
    elif total_signal >= 0.5:
        pressure = 'BUY'
        confidence = min(abs(total_signal) / num_indicators * 100, 100)
    elif total_signal <= -2:
        pressure = 'STRONG_SELL'
        confidence = min(abs(total_signal) / num_indicators * 100, 100)
    elif total_signal <= -0.5:
        pressure = 'SELL'
        confidence = min(abs(total_signal) / num_indicators * 100, 100)
    else:
        pressure = 'NEUTRAL'
        confidence = 50

    return {
        'pressure': pressure,
        'obv_trend': obv_trend,
        'buy_sell_ratio': current_ratio,
        'ad_trend': ad_trend,
        'confidence': confidence,
        'obv_slope': obv_slope,
        'ad_slope': ad_slope
    }
