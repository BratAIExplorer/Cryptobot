import pandas as pd
import numpy as np
import os
from datetime import datetime

class DipBacktester:
    def __init__(self, csv_path, initial_capital=5000):
        self.csv_path = csv_path
        self.initial_capital = initial_capital
        self.balance = initial_capital
        self.positions = []
        self.trades = []
        
        # Performance metrics
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_profit = 0
        
    def load_data(self):
        print(f"Loading data from {self.csv_path}...")
        df = pd.read_csv(self.csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df

    def run(self, dip_threshold=-0.08, tp_pct=0.05, sl_pct=None):
        df = self.load_data()
        
        # Calculate 24h high for dip detection
        df['24h_high'] = df['high'].rolling(window=24).max()
        
        print(f"Starting backtest with {len(df)} candles...")
        
        for i in range(24, len(df)):
            row = df.iloc[i]
            current_price = row['close']
            high_24h = row['24h_high']
            
            # 1. Check Exit Conditions for open positions
            for pos in self.positions[:]:
                buy_price = pos['entry_price']
                pnl_pct = (current_price - buy_price) / buy_price
                
                # Take Profit
                if pnl_pct >= tp_pct:
                    self._close_position(pos, current_price, "TP")
                # Stop Loss (if enabled)
                elif sl_pct and pnl_pct <= -sl_pct:
                    self._close_position(pos, current_price, "SL")
            
            # 2. Check Entry Condition (Dip)
            drop_pct = (current_price - high_24h) / high_24h
            if drop_pct <= dip_threshold:
                # Avoid overlapping positions for the same bot in backtest for simplicity
                if not self.positions:
                    self._open_position(current_price, row['timestamp'])

        self._print_stats()

    def _open_position(self, price, timestamp):
        # Using a fixed $500 per tranche
        tranche_size = 500
        if self.balance >= tranche_size:
            amount = tranche_size / price
            self.balance -= tranche_size
            pos = {
                'entry_price': price,
                'amount': amount,
                'entry_time': timestamp,
                'cost': tranche_size
            }
            self.positions.append(pos)

    def _close_position(self, pos, price, reason):
        sell_value = pos['amount'] * price
        
        # Apply MEXC Fees (0.1%) and Slippage (0.1%)
        total_fees = sell_value * 0.002 
        net_proceeds = sell_value - total_fees
        
        profit = net_proceeds - pos['cost']
        profit_pct = (profit / pos['cost']) * 100
        
        self.balance += net_proceeds
        self.total_profit += profit
        self.total_trades += 1
        
        if profit > 0:
            self.wins += 1
        else:
            self.losses += 1
            
        self.trades.append({
            'entry_time': pos['entry_time'],
            'profit_usd': profit,
            'profit_pct': profit_pct,
            'reason': reason
        })
        self.positions.remove(pos)

    def _print_stats(self):
        print("\n" + "="*30)
        print("📊 BACKTEST RESULTS 📊")
        print("="*30)
        print(f"Total Trades: {self.total_trades}")
        print(f"Wins: {self.wins}")
        print(f"Losses: {self.losses}")
        win_rate = (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Net Profit: ${self.total_profit:.2f}")
        print(f"Final Balance: ${self.balance:.2f}")
        print("="*30)

if __name__ == "__main__":
    # Point to your historical data
    data_file = 'data/mexc_history/BTC_USDT_1h_12m.csv'
    if os.path.exists(data_file):
        tester = DipBacktester(data_file, initial_capital=10000)
        # Parameters: 8% drop, 5% TP, No Stop Loss (Senior Trader Strategy)
        print("🚀 Running Buy-The-Dip backtest for BTC...")
        tester.run(dip_threshold=-0.08, tp_pct=0.05)
    else:
        print(f"❌ Data file not found: {data_file}")
