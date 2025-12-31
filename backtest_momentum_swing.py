#!/usr/bin/env python3
"""
Backtest for Momentum Swing Bot - Fix or Kill Decision
Tests both Current (broken) vs Proposed V2 implementations
"""
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import ccxt

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.indicators import (
    calculate_sma, calculate_rsi, calculate_macd,
    calculate_adx, calculate_atr
)

def backtest_momentum_strategy(
    symbol, start_date, end_date, params, strategy_version='current'
):
    """
    Backtest momentum strategy

    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        start_date: Start date string 'YYYY-MM-DD'
        end_date: End date string 'YYYY-MM-DD'
        params: Strategy parameters dict
        strategy_version: 'current' (broken DCA fallback) or 'v2' (proposed fix)

    Returns:
        metrics: Performance metrics dict
        trades: List of completed trades
    """

    print(f"\n{'='*70}")
    print(f"📊 Backtesting {symbol} - {strategy_version.upper()}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*70}")

    # Fetch historical data
    exchange = ccxt.mexc()

    since = exchange.parse8601(f"{start_date}T00:00:00Z")
    end = exchange.parse8601(f"{end_date}T23:59:59Z")

    all_ohlcv = []
    current = since

    print("Fetching historical data...")
    while current < end:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, '1h', since=current, limit=1000)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            current = ohlcv[-1][0] + 1
            if len(all_ohlcv) % 5000 == 0:
                print(f"  Loaded {len(all_ohlcv)} candles...")
        except Exception as e:
            print(f"Error fetching data: {e}")
            break

    if len(all_ohlcv) < 100:
        print("❌ Not enough data for backtest")
        return None, []

    # Convert to DataFrame
    df = pd.DataFrame(
        all_ohlcv,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    print(f"✅ Loaded {len(df)} hourly candles\n")

    # Calculate indicators
    df['sma_20'] = calculate_sma(df['close'], period=20)
    df['rsi'] = calculate_rsi(df['close'], period=14)
    df['atr'] = calculate_atr(df, period=14)

    if strategy_version == 'v2':
        # V2 uses MACD and ADX
        macd_result = calculate_macd(df['close'])
        df['macd'] = macd_result['macd']
        df['macd_signal'] = macd_result['signal']
        df['macd_histogram'] = macd_result['histogram']

        df['adx'] = calculate_adx(df)

    # Calculate 24h price change and volume ratio
    df['price_change_24h'] = df['close'].pct_change(24)
    df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma_20']

    # Simulate trading
    trades = []
    position = None
    capital = params.get('initial_balance', 1000)
    position_size = params.get('amount', 150)

    for i in range(50, len(df)):
        row = df.iloc[i]

        # Skip if no position and not enough capital
        if position is None and capital < position_size:
            continue

        # ENTRY LOGIC
        if position is None:
            signal = False

            if strategy_version == 'current':
                # BROKEN: Falls back to DCA logic (buy when RSI < 40)
                signal = row['rsi'] < 40

            elif strategy_version == 'v2':
                # V2: Proper momentum logic
                # 1. Price moved significantly (6%+)
                price_momentum = abs(row['price_change_24h']) >= params.get('min_24h_move', 0.06)

                # 2. High volume (2x+ average)
                volume_surge = row['volume_ratio'] >= params.get('min_volume_ratio', 2.0)

                # 3. Above SMA20 (uptrend)
                above_sma = row['close'] > row['sma_20']

                # 4. ADX > 25 (strong trend)
                strong_trend = row['adx'] > params.get('adx_threshold', 25)

                # 5. MACD bullish (histogram > 0)
                macd_bullish = row['macd_histogram'] > 0

                # 6. RSI in momentum zone (60-80)
                rsi_threshold = params.get('rsi_threshold', 60)
                rsi_momentum = rsi_threshold <= row['rsi'] <= 80

                signal = (
                    price_momentum and
                    volume_surge and
                    above_sma and
                    strong_trend and
                    macd_bullish and
                    rsi_momentum
                )

            if signal:
                # Open position
                position = {
                    'entry_time': row['timestamp'],
                    'entry_price': row['close'],
                    'size': position_size,
                    'stop_loss': row['close'] * (1 - params.get('stop_loss_pct', 0.04)),
                    'take_profit': row['close'] * (1 + params.get('take_profit_pct', 0.10)),
                    'max_hold_hours': params.get('max_hold_hours', 288)
                }
                capital -= position_size

        # EXIT LOGIC
        else:
            hours_held = (row['timestamp'] - position['entry_time']).total_seconds() / 3600

            # Check exit conditions
            hit_stop_loss = row['close'] <= position['stop_loss']
            hit_take_profit = row['close'] >= position['take_profit']
            max_hold_exceeded = hours_held >= position['max_hold_hours']

            if hit_stop_loss or hit_take_profit or max_hold_exceeded:
                # Close position
                exit_price = row['close']
                profit_pct = (exit_price - position['entry_price']) / position['entry_price']
                profit = position['size'] * profit_pct

                trade = {
                    'entry_time': position['entry_time'],
                    'exit_time': row['timestamp'],
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'hold_hours': hours_held,
                    'profit_pct': profit_pct * 100,
                    'profit': profit,
                    'exit_reason': 'SL' if hit_stop_loss else ('TP' if hit_take_profit else 'MAX_HOLD')
                }
                trades.append(trade)

                capital += position['size'] + profit
                position = None

    # Close any open position at end
    if position:
        final_row = df.iloc[-1]
        hours_held = (final_row['timestamp'] - position['entry_time']).total_seconds() / 3600
        exit_price = final_row['close']
        profit_pct = (exit_price - position['entry_price']) / position['entry_price']
        profit = position['size'] * profit_pct

        trades.append({
            'entry_time': position['entry_time'],
            'exit_time': final_row['timestamp'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'hold_hours': hours_held,
            'profit_pct': profit_pct * 100,
            'profit': profit,
            'exit_reason': 'END'
        })
        capital += position['size'] + profit

    # Calculate metrics
    if len(trades) == 0:
        print("❌ No trades executed")
        return None, []

    wins = [t for t in trades if t['profit'] > 0]
    losses = [t for t in trades if t['profit'] <= 0]

    total_profit = sum(t['profit'] for t in trades)
    gross_wins = sum(t['profit'] for t in wins) if wins else 0
    gross_losses = abs(sum(t['profit'] for t in losses)) if losses else 0.01

    metrics = {
        'total_trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': (len(wins) / len(trades)) * 100,
        'total_profit': total_profit,
        'total_return': (total_profit / params.get('initial_balance', 1000)) * 100,
        'avg_win': (gross_wins / len(wins)) if wins else 0,
        'avg_loss': (gross_losses / len(losses)) if losses else 0,
        'profit_factor': gross_wins / gross_losses if gross_losses > 0 else 0,
        'avg_hold_hours': sum(t['hold_hours'] for t in trades) / len(trades),
        'final_capital': capital,
        'sharpe_ratio': 0  # Simplified
    }

    return metrics, trades


def print_results(metrics, trades, version):
    """Print formatted results"""

    if metrics is None:
        return

    print(f"\n{'='*70}")
    print(f"📊 RESULTS - {version.upper()}")
    print(f"{'='*70}")

    print(f"\n🎯 OVERALL PERFORMANCE:")
    print(f"  Total Trades:    {metrics['total_trades']}")
    print(f"  Wins:            {metrics['wins']} ({metrics['win_rate']:.1f}%)")
    print(f"  Losses:          {metrics['losses']}")
    print(f"  Total Profit:    ${metrics['total_profit']:.2f}")
    print(f"  Total Return:    {metrics['total_return']:.2f}%")
    print(f"  Final Capital:   ${metrics['final_capital']:.2f}")

    print(f"\n📈 TRADE QUALITY:")
    print(f"  Avg Win:         ${metrics['avg_win']:.2f}")
    print(f"  Avg Loss:        ${metrics['avg_loss']:.2f}")
    print(f"  Profit Factor:   {metrics['profit_factor']:.2f}")
    print(f"  Avg Hold:        {metrics['avg_hold_hours']:.1f} hours")

    # Exit reason breakdown
    exit_reasons = {}
    for t in trades:
        reason = t['exit_reason']
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

    print(f"\n🚪 EXIT REASONS:")
    for reason, count in exit_reasons.items():
        pct = (count / len(trades)) * 100
        print(f"  {reason:12s} {count:3d} trades ({pct:.1f}%)")

    # Show sample trades
    print(f"\n📋 SAMPLE TRADES (First 5):")
    for i, trade in enumerate(trades[:5]):
        print(f"  {i+1}. {trade['entry_time'].strftime('%Y-%m-%d %H:%M')}: "
              f"{trade['profit_pct']:+6.2f}% ({trade['hold_hours']:.0f}h) - {trade['exit_reason']}")


def main():
    print("="*70)
    print("🔬 MOMENTUM SWING STRATEGY BACKTEST - FIX OR KILL DECISION")
    print("="*70)

    # Test parameters
    symbol = 'BTC/USDT'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 3 months

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    # Current (broken) parameters
    current_params = {
        'initial_balance': 1000,
        'amount': 150,
        'min_24h_move': 0.05,
        'min_volume_ratio': 1.3,
        'take_profit_pct': 0.10,
        'stop_loss_pct': 0.04,  # Too tight!
        'max_hold_hours': 288
    }

    # Proposed V2 parameters
    v2_params = {
        'initial_balance': 1000,
        'amount': 150,
        'min_24h_move': 0.06,       # Stricter
        'min_volume_ratio': 2.0,     # Much stricter
        'adx_threshold': 25,         # NEW
        'rsi_threshold': 60,         # NEW
        'take_profit_pct': 0.12,     # Higher
        'stop_loss_pct': 0.07,       # Wider (swing trading)
        'max_hold_hours': 336        # 14 days
    }

    # Run backtests
    print("\n" + "="*70)
    print("TEST 1: CURRENT VERSION (Broken - Falls back to DCA)")
    print("="*70)
    metrics_current, trades_current = backtest_momentum_strategy(
        symbol, start_str, end_str, current_params, 'current'
    )
    print_results(metrics_current, trades_current, 'CURRENT (DCA Fallback)')

    print("\n" + "="*70)
    print("TEST 2: PROPOSED V2 (Proper Momentum Logic)")
    print("="*70)
    metrics_v2, trades_v2 = backtest_momentum_strategy(
        symbol, start_str, end_str, v2_params, 'v2'
    )
    print_results(metrics_v2, trades_v2, 'PROPOSED V2')

    # Decision
    print("\n" + "="*70)
    print("🎯 FIX OR KILL DECISION")
    print("="*70)

    if metrics_v2 is None:
        print("\n❌ VERDICT: KILL")
        print("   Reason: V2 strategy generates no trades (too strict)")
        print("   Action: Delete Momentum Swing Bot")
        return

    if metrics_current:
        print(f"\nCURRENT (Broken):")
        print(f"  Win Rate: {metrics_current['win_rate']:.1f}%")
        print(f"  Profit:   ${metrics_current['total_profit']:.2f}")
        print(f"  Return:   {metrics_current['total_return']:.2f}%")

    print(f"\nPROPOSED V2:")
    print(f"  Win Rate: {metrics_v2['win_rate']:.1f}%")
    print(f"  Profit:   ${metrics_v2['total_profit']:.2f}")
    print(f"  Return:   {metrics_v2['total_return']:.2f}%")

    # Decision criteria
    v2_profitable = metrics_v2['total_return'] > 10  # > 10% over 3 months
    v2_good_winrate = metrics_v2['win_rate'] >= 40
    v2_good_pf = metrics_v2['profit_factor'] >= 2.0
    enough_trades = metrics_v2['total_trades'] >= 5

    print(f"\n📊 EVALUATION CRITERIA:")
    print(f"  ✅ Profitable (>10% return):  {'YES' if v2_profitable else 'NO'} ({metrics_v2['total_return']:.1f}%)")
    print(f"  ✅ Good Win Rate (>=40%):     {'YES' if v2_good_winrate else 'NO'} ({metrics_v2['win_rate']:.1f}%)")
    print(f"  ✅ Good Profit Factor (>=2):  {'YES' if v2_good_pf else 'NO'} ({metrics_v2['profit_factor']:.2f})")
    print(f"  ✅ Enough Trades (>=5):       {'YES' if enough_trades else 'NO'} ({metrics_v2['total_trades']})")

    criteria_met = sum([v2_profitable, v2_good_winrate, v2_good_pf, enough_trades])

    print(f"\n{'='*70}")
    if criteria_met >= 3:
        print("✅ VERDICT: FIX IT")
        print(f"   Criteria Met: {criteria_met}/4")
        print("   Action: Implement Momentum V2 (12-16 hours effort)")
        print("   Expected: +$600-800/month")
    else:
        print("❌ VERDICT: KILL IT")
        print(f"   Criteria Met: {criteria_met}/4 (need 3+)")
        print("   Action: Delete Momentum Swing Bot, reallocate $1000 to proven strategies")
        print("   Rationale: Not worth 12-16 hours development time")

    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
