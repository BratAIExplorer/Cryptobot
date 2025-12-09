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

def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range (ATR)"""
    # TR = Max(High-Low, Abs(High-PrevClose), Abs(Low-PrevClose))
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    
    return true_range.rolling(window=period).mean()
