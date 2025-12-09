import requests
from utils.indicators import calculate_rsi, calculate_sma

class ConfluenceFilter:
    """
    Calculates a 0-100 Confluence Score for trade entries.
    Pillars:
    1. Technical (30pts): RSI
    2. Trend (30pts): Price > SMA200 & BTC > SMA200
    3. News (20pts): Sentiment from CryptoPanic (Mocked for now)
    4. Volume (20pts): Spike detection
    """
    
    def __init__(self, exchange=None):
        self.exchange = exchange # Hook to fetch BTC/ETH data if needed

    def calculate_score(self, df, btc_df=None):
        """
        Calculate total confluence score.
        Args:
            df: DataFrame for the target coin (must have close, volume)
            btc_df: DataFrame for BTC (for macro trend check)
        Returns:
            int: 0-100 score
        """
        score = 0
        details = []

        # 1. Technical (RSI) - Max 30 pts
        rsi = calculate_rsi(df['close']).iloc[-1]
        tech_score = 0
        if rsi < 30:
            tech_score = 30
        elif rsi < 40:
            tech_score = 20
        elif rsi < 50:
            tech_score = 10
        score += tech_score
        details.append(f"Tech: {tech_score}pts (RSI {rsi:.1f})")

        # 2. Trend (SMA 200) - Max 30 pts
        # Price vs SMA 200
        current_price = df['close'].iloc[-1]
        if len(df) >= 200:
            sma200 = calculate_sma(df['close'], period=200).iloc[-1]
            if current_price > sma200:
                score += 15
                details.append("Trend(Self): 15pts (>SMA200)")
            else:
                details.append("Trend(Self): 0pts (<SMA200)")
        
        # BTC Trend (Macro)
        if btc_df is not None and len(btc_df) >= 200:
            btc_price = btc_df['close'].iloc[-1]
            btc_sma200 = calculate_sma(btc_df['close'], period=200).iloc[-1]
            if btc_price > btc_sma200:
                score += 15
                details.append("Trend(BTC): 15pts (>SMA200)")
            else:
                score -= 20 # Penalty for Bear Market
                details.append("Trend(BTC): -20pts (<SMA200 - Bear Market Penalty)")

        # 3. Volume - Max 20 pts
        if 'volume' in df.columns:
            avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
            curr_vol = df['volume'].iloc[-1]
            if curr_vol > 1.5 * avg_vol:
                score += 20
                details.append(f"Vol: 20pts ({curr_vol/avg_vol:.1f}x)")
            elif curr_vol > 1.0 * avg_vol:
                score += 10
                details.append(f"Vol: 10pts ({curr_vol/avg_vol:.1f}x)")
        
        # 4. News (Placeholder) - Max 20 pts
        # In Phase 2, integrate CryptoPanic API. 
        # For now, assume Neutral (10pts) to avoid blocking trades completely.
        score += 10
        details.append("News: 10pts (Neutral - Placeholder)")

        # Cap min/max
        final_score = max(0, min(100, score))
        return final_score, details

