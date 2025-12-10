import requests
import pandas as pd
import numpy as np

# --- 1. Data Fetcher (Binance API) ---
def fetch_binance_data(symbol, interval='15m', limit=1000):
    """
    Fetch last 1000 candles (approx 10 days of 15m data)
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol.replace('/', ''),
        'interval': interval,
        'limit': limit
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # Check for error response
        if isinstance(data, dict) and 'code' in data:
            print(f"Error fetching {symbol}: {data['msg']}")
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        return df
    except Exception as e:
        print(f"Exception fetching {symbol}: {e}")
        return pd.DataFrame()

# --- 2. Indicators ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- 3. Simulation Engine ---
def run_simulation(df, rsi_limit, rsi_period=14):
    """
    Simulate RSI Scalper.
    Rules:
    - BUY when RSI < rsi_limit
    - SELL when Profit > 3% OR Loss < -5% (Stop Loss)
    """
    balance = 1000.0 # Starting simulated cash
    position = None # {'price': float, 'amount': float}
    trades = []
    
    # Calculate RSI
    # We allow the period to vary, but usually people tweak the Limit (30 vs 20) 
    # OR the Period (14 vs 7). The user asked for "RSI 7", implying Period=7.
    # Note: "RSI 7" usually means Period=7. "RSI < 30" is the limit.
    # We will assume user means Period=N, and we keep limit standard at 30?
    # Or maybe user means Limit=10? 
    # Context usually implies Period=14 is standard, so "RSI 7" means Period=7.
    # Let's assume Limit is constant at 30 for fair comparison, changing ONLY Period.
    
    df['rsi'] = calculate_rsi(df['close'], period=rsi_period)
    
    # Trading Loop
    for i, row in df.iterrows():
        if i < rsi_period: continue
        
        current_price = row['close']
        current_rsi = row['rsi']
        
        # Logic
        if position:
            # Check for Sell
            entry_price = position['price']
            pct_change = (current_price - entry_price) / entry_price
            
            # TP: +3%, SL: -5%
            if pct_change >= 0.03 or pct_change <= -0.05:
                # Execute SELL
                revenue = position['amount'] * current_price
                profit = revenue - 1000 # Profit per trade normalized to investment
                # Actually, simplified:
                pnl = (pct_change * 1000) # Assuming fixed bet size of $1000
                
                balance += pnl
                trades.append({
                    'side': 'SELL',
                    'price': current_price,
                    'pnl': pnl,
                    'reason': f"{'TP' if pct_change > 0 else 'SL'} ({pct_change*100:.1f}%)"
                })
                position = None
        else:
            # Check for Buy
            if current_rsi < 30: # Standard oversold threshold
                # Execute BUY
                cost = 1000 # Fixed bet size
                amount = cost / current_price
                position = {
                    'price': current_price,
                    'amount': amount
                }
                # No trade log for buy, only sell matters for PnL list
    
    # Check open position at end
    if position:
        final_price = df.iloc[-1]['close']
        pct_change = (final_price - position['price']) / position['price']
        pnl = (pct_change * 1000)
        balance += pnl # Unrealized PnL
        
    return {
        'final_balance': balance,
        'profit': balance - 1000,
        'trade_count': len(trades)
    }

# --- 4. Main Controller ---
def main():
    print("==================================================")
    print("🧪 RSI STRATEGY BACKTEST (Period: 7 vs 10 vs 14)")
    print("   Data: Binance (Last 10 Days, 15m candles)")
    print("   Rules: Buy if RSI < 30. Sell if +3% or -5%.")
    print("==================================================\n")
    
    coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'DOGE/USDT']
    periods = [7, 10, 14]
    
    results = []
    
    for coin in coins:
        print(f"Downloading {coin}...")
        df = fetch_binance_data(coin)
        
        if df.empty:
            continue
            
        for p in periods:
            res = run_simulation(df, rsi_limit=30, rsi_period=p)
            results.append({
                'coin': coin,
                'period': p,
                'profit': res['profit'],
                'trades': res['trade_count']
            })
            
    # Summary Table
    print("\n--- RESULTS SUMMARY ---")
    print(f"{'COIN':<10} | {'RSI PERIOD':<10} | {'PROFIT ($)':<12} | {'TRADES':<8}")
    print("-" * 50)
    
    # Group by Period for final score
    score = {7: 0.0, 10: 0.0, 14: 0.0}
    
    for r in results:
        print(f"{r['coin']:<10} | RSI {r['period']:<6} | ${r['profit']:>9.2f} | {r['trades']:<8}")
        score[r['period']] += r['profit']
        
    print("\n==================================================")
    print("🏆 GRAND CHAMPION")
    print("==================================================")
    for p, total in score.items():
        print(f"RSI {p:<2}: Total Profit ${total:.2f}")

    winner = max(score, key=score.get)
    print(f"\n✅ WINNER: RSI {winner}")

if __name__ == "__main__":
    main()
