import requests
import pandas as pd
import numpy as np
from strategies.grid_strategy_v2 import GridStrategyV2

def fetch_binance_data(symbol, interval='1h', limit=720):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol.replace('/', ''),
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    return df

def run_backtest(df, config):
    strategy = GridStrategyV2(config)
    
    balance = config.get('initial_balance', 1000)
    positions = [] # List of dicts: {'id': int, 'buy_price': float, 'amount': float}
    trades = []
    
    position_counter = 0
    
    for i, row in df.iterrows():
        current_price = row['close']
        
        # Mock open_positions dataframe
        if positions:
            open_positions_df = pd.DataFrame(positions)
        else:
            open_positions_df = pd.DataFrame(columns=['id', 'buy_price', 'amount'])
            
        signal = strategy.get_signal(current_price, open_positions_df)
        
        if signal:
            if signal['side'] == 'BUY':
                cost = strategy.amount_per_grid
                if balance >= cost:
                    balance -= cost
                    position_counter += 1
                    positions.append({
                        'id': position_counter,
                        'buy_price': current_price,
                        'amount': cost / current_price
                    })
                    trades.append({'side': 'BUY', 'price': current_price, 'time': row['timestamp']})
                    
            elif signal['side'] == 'SELL':
                pos_id = signal['position_id']
                # Find and remove position
                pos = next((p for p in positions if p['id'] == pos_id), None)
                if pos:
                    positions.remove(pos)
                    revenue = pos['amount'] * current_price
                    balance += revenue
                    trades.append({'side': 'SELL', 'price': current_price, 'profit': revenue - strategy.amount_per_grid, 'time': row['timestamp']})

    # Calculate final value
    equity = balance
    for pos in positions:
        equity += pos['amount'] * df.iloc[-1]['close']
        
    return equity, len(trades)

def optimize_grid(symbol):
    print(f"Fetching data for {symbol}...")
    df = fetch_binance_data(symbol)
    current_price = df.iloc[-1]['close']
    print(f"Current Price: {current_price}")
    
    best_pnl = -np.inf
    best_config = None
    
    # Test different ranges and grid counts
    ranges = [0.1, 0.15, 0.2] # +/- 10%, 15%, 20%
    grid_counts = [10, 20, 30]
    
    print(f"Running optimization...")
    for r in ranges:
        for g in grid_counts:
            lower = current_price * (1 - r)
            upper = current_price * (1 + r)
            
            config = {
                'symbol': symbol,
                'lower_limit': lower,
                'upper_limit': upper,
                'grid_levels': g,
                'amount': 50,
                'initial_balance': 2000
            }
            
            final_equity, num_trades = run_backtest(df, config)
            pnl = final_equity - 2000
            
            print(f"Range: +/-{r*100}%, Grids: {g} -> PnL: ${pnl:.2f}, Trades: {num_trades}")
            
            if pnl > best_pnl:
                best_pnl = pnl
                best_config = config
                best_config['range_pct'] = r
                
    print("-" * 30)
    print(f"BEST CONFIG FOR {symbol}:")
    print(f"Range: +/-{best_config['range_pct']*100}% ({best_config['lower_limit']:.2f} - {best_config['upper_limit']:.2f})")
    print(f"Grids: {best_config['grid_levels']}")
    print(f"PnL: ${best_pnl:.2f}")
    return best_config

if __name__ == "__main__":
    optimize_grid('BTC/USDT')
    print("\n")
    optimize_grid('ETH/USDT')
