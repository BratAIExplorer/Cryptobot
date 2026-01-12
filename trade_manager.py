"""
CryptoBots V3 - Trade History Manager
Manages trade logging, retrieval, and detailed analytics.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class TradeManager:
    """
    Manages trade history with support for detailed indicators (RSI, etc.)
    and efficient filtering.
    """
    
    TRADE_FILE = Path("config/trades.json")
    
    def __init__(self):
        self.trades: List[Dict] = []
        self._load_trades()
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        self.TRADE_FILE.parent.mkdir(exist_ok=True)
    
    def _load_trades(self):
        """Load trades from JSON file."""
        if not self.TRADE_FILE.exists():
            return
            
        try:
            with open(self.TRADE_FILE, 'r') as f:
                self.trades = json.load(f)
            # Sort by timestamp descending (newest first)
            self.trades.sort(key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            print(f"❌ Failed to load trades: {e}")
            self.trades = []

    def _save_trades(self):
        """Save trades to JSON file."""
        try:
            # Save generic JSON
            with open(self.TRADE_FILE, 'w') as f:
                json.dump(self.trades, f, indent=2)
        except Exception as e:
            print(f"❌ Failed to save trades: {e}")

    def log_trade(self, bot_id: str, bot_name: str, symbol: str, 
                 side: str, price: float, amount: float, 
                 strategy: str, details: Dict = None):
        """
        Log a new trade with technical details.
        
        Args:
            bot_id: ID of the bot executing trade
            bot_name: Human readable bot name
            symbol: Trading pair (e.g. BTC/USDT)
            side: 'buy' or 'sell'
            price: Execution price
            amount: Quantity traded
            strategy: Strategy used (e.g. 'buy_dip')
            details: Dictionary of technicals (RSI, MA, breakdown info)
        """
        trade = {
            'id': f"trade_{len(self.trades) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'bot_id': bot_id,
            'bot_name': bot_name,
            'symbol': symbol,
            'side': side,
            'price': float(price),
            'amount': float(amount),
            'value': float(price * amount),
            'strategy': strategy,
            'details': details or {},
            'pnl': 0.0  # Filled on close
        }
        
        self.trades.insert(0, trade) # Add to top
        self._save_trades()
        return trade

    def get_trades(self, bot_id: str = None, limit: int = 50) -> List[Dict]:
        """
        Get trades with optional filtering.
        
        Args:
            bot_id: Filter by specific bot ID
            limit: Max trades to return (default 50)
            
        Returns:
            List of trade dictionaries
        """
        if bot_id:
            filtered = [t for t in self.trades if t['bot_id'] == bot_id]
            return filtered[:limit]
        
        return self.trades[:limit]

    def get_bot_stats(self, bot_id: str) -> Dict:
        """Get calculated stats for a bot from trade history."""
        bot_trades = [t for t in self.trades if t['bot_id'] == bot_id]
        
        if not bot_trades:
            return {'total_trades': 0, 'pnl': 0, 'win_rate': 0}
            
        pnl = sum(t.get('pnl', 0) for t in bot_trades)
        closed_trades = [t for t in bot_trades if t.get('pnl') != 0]
        wins = len([t for t in closed_trades if t['pnl'] > 0])
        
        win_rate = (wins / len(closed_trades) * 100) if closed_trades else 0
        
        return {
            'total_trades': len(bot_trades),
            'total_pnl': pnl,
            'win_rate': win_rate
        }

    def import_dummy_data(self):
        """Generate dummy data for demo purposes."""
        # Only if empty
        if self.trades:
            return

        print("Generating dummy trade history...")
        
        # We'll generate data matching the bots.json demo bots
        # 1. BTC Dip Hunter (Running, +15.30)
        # 2. ETH Aggressive (Paused, +8.20)
        # 3. BTC Profit (Running, +18.20)
        
        dummy_trades = [
            # Recent BTC Profit Trade
            {
                "timestamp": datetime.now().isoformat(),
                "bot_id": "demo_btc_profit_001",
                "bot_name": "BTC Profit Taker",
                "symbol": "BTC/USDT",
                "side": "sell",
                "price": 68250.00,
                "amount": 0.005,
                "value": 341.25,
                "pnl": 12.50,
                "strategy": "take_profit",
                "details": {
                    "reason": "Profit Target Hit",
                    "target_price": 68000.00,
                    "rsi_14": 72.5,
                    "trend": "Strong Uptrend"
                }
            },
            # BTC Dip Buy
            {
                "timestamp": (datetime.now()).isoformat(),
                "bot_id": "demo_btc_dip_001",
                "bot_name": "BTC Dip Hunter", 
                "symbol": "BTC/USDT",
                "side": "buy",
                "price": 66500.00,
                "amount": 0.008,
                "value": 532.00,
                "pnl": 0,
                "strategy": "buy_dip",
                "details": {
                    "reason": "Dip > 5%",
                    "dip_depth": "5.2%",
                    "24h_high": 70150.00,
                    "rsi_14": 28.4
                }
            },
            # ETH Trade (Closed)
            {
                "timestamp": datetime.now().isoformat(),
                "bot_id": "demo_eth_dip_001",
                "bot_name": "ETH Aggressive Dip",
                "symbol": "ETH/USDT",
                "side": "sell",
                "price": 2650.00,
                "amount": 0.5,
                "value": 1325.00,
                "pnl": 8.20,
                "strategy": "buy_dip", 
                "details": {
                    "reason": "Trailing Stop Hit",
                    "stop_price": 2645.00,
                    "rsi_14": 68.0
                }
            },
             # Earlier BTC Trade
            {
                "timestamp": datetime.now().isoformat(),
                "bot_id": "demo_btc_profit_001",
                "bot_name": "BTC Profit Taker",
                "symbol": "BTC/USDT",
                "side": "buy",
                "price": 67000.00,
                "amount": 0.005,
                "value": 335.00,
                "pnl": 0,
                "strategy": "take_profit",
                "details": {
                    "reason": "Entry Signal",
                    "rsi_14": 45.0,
                    "adx": 35.0
                }
            }
        ]
        
        self.trades = dummy_trades
        self._save_trades()

if __name__ == "__main__":
    tm = TradeManager()
    tm.import_dummy_data()
    print("✅ Generated dummy trades")
