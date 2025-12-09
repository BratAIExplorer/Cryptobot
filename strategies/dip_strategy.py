from .base_strategy import BaseStrategy
from utils.confluence_filter import ConfluenceFilter
import pandas as pd

class DipStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.amount = config.get('amount', 50) # Standard $50 buys
        self.confluence_engine = ConfluenceFilter()
        self.min_confluence = 50

    def generate_signal(self, df, btc_df=None):
        """
        Buy-The-Dip: Only buy if Confluence Score >= 50.
        """
        if df.empty:
            return None
            
        # 1. Calculate Confluence Score
        score, details = self.confluence_engine.calculate_score(df, btc_df)
        
        # 2. Check Threshold
        if score >= self.min_confluence:
            return {
                'side': 'BUY',
                'amount': self.amount,
                'reason': f"Confluence Score {score}/100 | {' | '.join(details)}"
            }
            
        # Log skipped opportunities if score is close (optional debugging)
        # if score > 30:
        #    print(f"[DIP SKIP] Score {score} < 50: {details}")

        return None
