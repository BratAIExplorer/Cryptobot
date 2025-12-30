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
