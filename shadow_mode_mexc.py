#!/usr/bin/env python3
"""
MEXC Shadow Mode - Live Data, Paper Money Forward Test
Logs all trading signals without executing real orders
Tracks slippage, latency, and fee simulation
"""
import sys
import os
import csv
from datetime import datetime, timedelta
import time
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.exchange_mexc import MEXCExchange
from core.logger import TradeLogger
from utils.indicators import calculate_rsi, calculate_sma

class ShadowModeValidator:
    """
    Shadow Mode Trading Simulator
    - Receives real-time MEXC market data
    - Logs buy/sell signals
    - Simulates fills with MEXC fees (0.05% taker)
    - Tracks slippage by comparing signal price to T+5s actual price
    """
    
    def __init__(self, output_file='shadow_mode_trades.csv'):
        self.exchange = MEXCExchange(mode='paper')
        self.logger = TradeLogger(mode='shadow')  # New shadow mode DB
        self.output_file = output_file
        self.simulated_balance = 5000.0  # Start with $5000 virtual capital
        self.simulated_positions = {}  # Track open shadow positions
        
        # Initialize CSV log
        self._init_csv_log()
        
        print("=" * 80)
        print("🎭 MEXC SHADOW MODE VALIDATOR")
        print("=" * 80)
        print(f"📊 Real-time data source: MEXC Exchange")
        print(f"💰 Virtual capital: ${self.simulated_balance:,.2f}")
        print(f"📁 Output file: {self.output_file}")
        print(f"🔬 Testing period: 7 days (168 hours)")
        print("=" * 80)
    
    def _init_csv_log(self):
        """Initialize CSV file with headers"""
        headers = [
            'timestamp',
            'signal_timestamp',
            'strategy',
            'symbol',
            'signal_type',  # BUY or SELL
            'signal_price',
            'actual_price_t5s',  # Actual price 5 seconds later
            'slippage_pct',
            'latency_ms',
            'order_book_bid',
            'order_book_ask',
            'spread_pct',
            'estimated_fill_price',
            'simulated_fee',
            'simulated_pnl',
            'volume_24h_usd',
            'rsi',
            'notes'
        ]
        
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
    
    def _log_signal(self, signal_data):
        """Append a signal to CSV log"""
        with open(self.output_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=signal_data.keys())
            writer.writerow(signal_data)
    
    def _get_current_price_with_latency(self, symbol):
        """
        Fetch current price and measure API latency
        Returns: (price, latency_ms)
        """
        start_time = time.time()
        ticker = self.exchange.fetch_ticker(symbol)
        latency_ms = (time.time() - start_time) * 1000
        
        return ticker['last'], latency_ms
    
    def _estimate_slippage(self, symbol, signal_price, side, amount=400):
        """
        Estimate slippage by:
        1. Checking actual price 5 seconds after signal
        2. Analyzing order book depth
        """
        # Wait 5 seconds to simulate order execution delay
        time.sleep(5)
        actual_price, _ = self._get_current_price_with_latency(symbol)
        
        # Calculate slippage
        if side == 'BUY':
            slippage_pct = ((actual_price - signal_price) / signal_price) * 100
        else:  # SELL
            slippage_pct = ((signal_price - actual_price) / signal_price) * 100
        
        # Get order book for spread analysis
        order_book = self.exchange.get_order_book(symbol, limit=10)
        bid = order_book['bids'][0][0] if len(order_book['bids']) > 0 else 0
        ask = order_book['asks'][0][0] if len(order_book['asks']) > 0 else 0
        spread_pct = ((ask - bid) / bid * 100) if bid > 0 else 0
        
        # Estimate fill price using order book
        estimated_fill, estimated_slippage = self.exchange.estimate_slippage(symbol, side.lower(), amount)
        
        return {
            'actual_price_t5s': actual_price,
            'slippage_pct': slippage_pct,
            'order_book_bid': bid,
            'order_book_ask': ask,
            'spread_pct': spread_pct,
            'estimated_fill_price': estimated_fill or actual_price
        }
    
    def process_buy_signal(self, strategy, symbol, signal_price, rsi, amount=400):
        """
        Process a BUY signal in shadow mode
        """
        print(f"\n🟢 BUY SIGNAL: {strategy} - {symbol} @ ${signal_price:.4f} (RSI: {rsi:.1f})")
        
        signal_timestamp = datetime.now()
        
        # Capture current market state
        price, latency = self._get_current_price_with_latency(symbol)
        ticker = self.exchange.fetch_ticker(symbol)
        volume_24h = ticker.get('quoteVolume', 0)
        
        # Estimate slippage
        slippage_data = self._estimate_slippage(symbol, signal_price, 'BUY', amount)
        
        # Simulate order execution with MEXC fees
        fill_price = slippage_data['estimated_fill_price']
        fee = fill_price * amount * 0.0005  # 0.05% taker fee
        total_cost = (fill_price * amount) + fee
        
        # Check if we have virtual balance
        if total_cost > self.simulated_balance:
            print(f"   ⚠️ SKIPPED: Insufficient virtual balance (${self.simulated_balance:.2f} < ${total_cost:.2f})")
            return
        
        # Update virtual balance
        self.simulated_balance -= total_cost
        
        # Track position
        position_id = f"{symbol}_{int(signal_timestamp.timestamp())}"
        self.simulated_positions[position_id] = {
            'symbol': symbol,
            'strategy': strategy,
            'entry_price': fill_price,
            'amount': amount,
            'entry_fee': fee,
            'entry_time': signal_timestamp
        }
        
        # Log to CSV
        signal_data = {
            'timestamp': datetime.now().isoformat(),
            'signal_timestamp': signal_timestamp.isoformat(),
            'strategy': strategy,
            'symbol': symbol,
            'signal_type': 'BUY',
            'signal_price': signal_price,
            'latency_ms': latency,
            'volume_24h_usd': volume_24h,
            'rsi': rsi,
            'simulated_fee': fee,
            'simulated_pnl': 0.0,  # No PnL yet
            'notes': f'Position opened: {position_id}',
            **slippage_data
        }
        
        self._log_signal(signal_data)
        
        print(f"   ✅ SHADOW BUY EXECUTED")
        print(f"   💰 Fill Price: ${fill_price:.4f} (slippage: {slippage_data['slippage_pct']:.3f}%)")
        print(f"   💵 Fee: ${fee:.2f}")
        print(f"   📊 Remaining Balance: ${self.simulated_balance:.2f}")
    
    def process_sell_signal(self, strategy, symbol, signal_price, rsi, position_id=None):
        """
        Process a SELL signal in shadow mode
        """
        print(f"\n🔴 SELL SIGNAL: {strategy} - {symbol} @ ${signal_price:.4f} (RSI: {rsi:.1f})")
        
        # Find matching position
        matching_positions = [
            (pid, pos) for pid, pos in self.simulated_positions.items()
            if pos['symbol'] == symbol and pos['strategy'] == strategy
        ]
        
        if not matching_positions:
            print(f"   ⚠️ SKIPPED: No open position found for {symbol}")
            return
        
        # Close oldest position (FIFO)
        position_id, position = matching_positions[0]
        
        signal_timestamp = datetime.now()
        
        # Capture current market state
        price, latency = self._get_current_price_with_latency(symbol)
        
        # Estimate slippage
        slippage_data = self._estimate_slippage(symbol, signal_price, 'SELL', position['amount'])
        
        # Simulate order execution with MEXC fees
        fill_price = slippage_data['estimated_fill_price']
        gross_proceeds = fill_price * position['amount']
        exit_fee = gross_proceeds * 0.0005  # 0.05% taker fee
        net_proceeds = gross_proceeds - exit_fee
        
        # Calculate PnL
        cost_basis = (position['entry_price'] * position['amount']) + position['entry_fee']
        pnl = net_proceeds - cost_basis
        pnl_pct = (pnl / cost_basis) * 100
        
        # Hold duration
        hold_duration = (signal_timestamp - position['entry_time']).total_seconds() / 3600  # hours
        
        # Update virtual balance
        self.simulated_balance += net_proceeds
        
        # Remove position
        del self.simulated_positions[position_id]
        
        # Log to CSV
        signal_data = {
            'timestamp': datetime.now().isoformat(),
            'signal_timestamp': signal_timestamp.isoformat(),
            'strategy': strategy,
            'symbol': symbol,
            'signal_type': 'SELL',
            'signal_price': signal_price,
            'latency_ms': latency,
            'volume_24h_usd': 0,  # Not critical for sell
            'rsi': rsi,
            'simulated_fee': exit_fee,
            'simulated_pnl': pnl,
            'notes': f'Position closed: {position_id}, Hold: {hold_duration:.1f}h, PnL: {pnl_pct:.2f}%',
            **slippage_data
        }
        
        self._log_signal(signal_data)
        
        print(f"   ✅ SHADOW SELL EXECUTED")
        print(f"   💰 Fill Price: ${fill_price:.4f} (slippage: {slippage_data['slippage_pct']:.3f}%)")
        print(f"   💵 Exit Fee: ${exit_fee:.2f}")
        print(f"   📈 PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        print(f"   📊 New Balance: ${self.simulated_balance:.2f}")
    
    def generate_summary_report(self):
        """
        Generate summary statistics from shadow mode testing
        """
        # Read CSV log
        df = pd.read_csv(self.output_file)
        
        print("\n" + "=" * 80)
        print("📊 SHADOW MODE SUMMARY REPORT")
        print("=" * 80)
        
        # Overall statistics
        total_signals = len(df)
        buy_signals = len(df[df['signal_type'] == 'BUY'])
        sell_signals = len(df[df['signal_type'] == 'SELL'])
        
        print(f"\n📈 Signal Statistics:")
        print(f"   Total Signals: {total_signals}")
        print(f"   Buy Signals: {buy_signals}")
        print(f"   Sell Signals: {sell_signals}")
        
        # Slippage analysis
        avg_slippage = df['slippage_pct'].mean()
        max_slippage = df['slippage_pct'].max()
        p95_slippage = df['slippage_pct'].quantile(0.95)
        
        print(f"\n💨 Slippage Analysis:")
        print(f"   Average Slippage: {avg_slippage:.3f}%")
        print(f"   P95 Slippage: {p95_slippage:.3f}%")
        print(f"   Max Slippage: {max_slippage:.3f}%")
        
        # Latency analysis
        avg_latency = df['latency_ms'].mean()
        p95_latency = df['latency_ms'].quantile(0.95)
        
        print(f"\n⚡ API Latency:")
        print(f"   Average: {avg_latency:.0f}ms")
        print(f"   P95: {p95_latency:.0f}ms")
        
        # Spread analysis
        avg_spread = df['spread_pct'].mean()
        
        print(f"\n📏 Spread Analysis:")
        print(f"   Average Spread: {avg_spread:.3f}%")
        
        # PnL analysis (sell signals only)
        sell_df = df[df['signal_type'] == 'SELL']
        if len(sell_df) > 0:
            total_pnl = sell_df['simulated_pnl'].sum()
            winning_trades = len(sell_df[sell_df['simulated_pnl'] > 0])
            losing_trades = len(sell_df[sell_df['simulated_pnl'] < 0])
            win_rate = (winning_trades / len(sell_df)) * 100 if len(sell_df) > 0 else 0
            
            print(f"\n💰 Simulated Performance:")
            print(f"   Completed Trades: {len(sell_df)}")
            print(f"   Total PnL: ${total_pnl:.2f}")
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   Final Virtual Balance: ${self.simulated_balance:.2f}")
            print(f"   ROI: {((self.simulated_balance - 5000) / 5000) * 100:.2f}%")
        
        # Success criteria check
        print(f"\n✅ SUCCESS CRITERIA CHECK:")
        print(f"   [ {'✅' if p95_slippage < 0.5 else '❌'} ] P95 Slippage < 0.5%: {p95_slippage:.3f}%")
        print(f"   [ {'✅' if avg_spread < 0.3 else '❌'} ] Avg Spread < 0.3%: {avg_spread:.3f}%")
        print(f"   [ {'✅' if p95_latency < 2000 else '❌'} ] P95 Latency < 2000ms: {p95_latency:.0f}ms")
        if len(sell_df) > 0:
            print(f"   [ {'✅' if win_rate >= 50 else '❌'} ] Win Rate ≥ 50%: {win_rate:.1f}%")
        
        print("=" * 80)
        
        return {
            'avg_slippage': avg_slippage,
            'p95_slippage': p95_slippage,
            'avg_latency': avg_latency,
            'p95_latency': p95_latency,
            'avg_spread': avg_spread,
            'win_rate': win_rate if len(sell_df) > 0 else 0,
            'total_pnl': total_pnl if len(sell_df) > 0 else 0
        }

if __name__ == "__main__":
    # Example usage - integrate this with your existing run_bot.py
    validator = ShadowModeValidator()
    
    # Test signals (replace with your actual strategy logic)
    print("\nℹ️  Shadow mode validator initialized.")
    print("   Integrate this with your run_bot.py to capture live signals.")
    print("   After 48-168 hours, run validator.generate_summary_report()")
