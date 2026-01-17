#!/usr/bin/env python3
"""
Simple Real-Time Bot Diagnostic Tool
Uses CCXT directly - no custom adapters needed
"""

import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime
import numpy as np

# Try to import ccxt
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    print("⚠️  CCXT not available - install with: pip3 install ccxt")
    CCXT_AVAILABLE = False

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
RESET = '\033[0m'
BOLD = '\033[1m'


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    if down == 0:
        return 100
    rs = up/down
    rsi = 100 - (100/(1+rs))
    return rsi


class SimpleBotDiagnostic:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'data', 'multi', 'trades_paper.db')
        self.exchange = None

        if CCXT_AVAILABLE:
            try:
                self.exchange = ccxt.binance({'enableRateLimit': True})
                print(f"{GREEN}✓ Binance exchange initialized via CCXT{RESET}\n")
            except Exception as e:
                print(f"{RED}✗ Failed to initialize exchange: {e}{RESET}\n")

    def get_price_data(self, symbol):
        """Fetch price data from Binance"""
        if not self.exchange:
            return None

        try:
            # Convert symbol format (BTC/USDT -> BTCUSDT for Binance)
            binance_symbol = symbol.replace('/', '')

            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=50)

            if not ohlcv:
                return None

            # Convert to dataframe
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            return df
        except Exception as e:
            print(f"{RED}✗ Error fetching {symbol}: {e}{RESET}")
            return None

    def get_open_positions(self, bot_name=None):
        """Get open positions from database"""
        if not os.path.exists(self.db_path):
            print(f"{RED}✗ Database not found: {self.db_path}{RESET}")
            return pd.DataFrame()

        try:
            conn = sqlite3.connect(self.db_path)

            # Check columns
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(positions)")
            columns = [row[1] for row in cursor.fetchall()]

            # Adapt column names
            price_col = 'price' if 'price' in columns else 'buy_price'
            time_col = 'timestamp' if 'timestamp' in columns and 'buy_timestamp' not in columns else 'buy_timestamp'

            query = f"""
                SELECT id, strategy, symbol, amount, {price_col} as buy_price, {time_col} as buy_timestamp
                FROM positions
                WHERE status = 'OPEN'
            """
            if bot_name:
                query += f" AND strategy = '{bot_name}'"

            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"{RED}✗ Error reading positions: {e}{RESET}")
            return pd.DataFrame()

    def diagnose_grid_bot(self, name, symbol, config):
        """Diagnose Grid Bot"""
        print(f"{BOLD}{CYAN}{'='*100}{RESET}")
        print(f"{BOLD}{CYAN}🤖 {name} - {symbol}{RESET}")
        print(f"{CYAN}{'='*100}{RESET}\n")

        # Get price data
        df = self.get_price_data(symbol)

        if df is None or df.empty:
            print(f"{RED}✗ Cannot fetch price data for {symbol}{RESET}\n")
            return

        current_price = float(df['close'].iloc[-1])
        high_24h = float(df['high'].max())
        low_24h = float(df['low'].min())
        prices = df['close'].values
        rsi = calculate_rsi(prices)

        # Grid config
        lower = config['lower_limit']
        upper = config['upper_limit']
        levels = config['grid_levels']
        trade_size = config['amount']

        grids = np.linspace(lower, upper, levels)
        grid_step = (upper - lower) / (levels - 1)

        print(f"{BOLD}📊 MARKET STATUS{RESET}")
        print(f"├─ Current Price: ${current_price:,.2f}")
        print(f"├─ RSI (14):      {rsi:.1f}")
        print(f"├─ 24h High:      ${high_24h:,.2f}")
        print(f"├─ 24h Low:       ${low_24h:,.2f}")
        print(f"└─ 24h Range:     ${high_24h - low_24h:,.2f}\n")

        print(f"{BOLD}⚙️  GRID CONFIGURATION{RESET}")
        print(f"├─ Range:         ${lower:,} - ${upper:,} ({YELLOW}${upper-lower:,} spread{RESET})")
        print(f"├─ Grid Levels:   {levels}")

        if grid_step > 500:
            print(f"├─ Grid Step:     ${grid_step:,.2f} {RED}← TOO WIDE (should be $100-250){RESET}")
        elif grid_step > 250:
            print(f"├─ Grid Step:     ${grid_step:,.2f} {YELLOW}← Wide (consider reducing){RESET}")
        else:
            print(f"├─ Grid Step:     ${grid_step:,.2f} {GREEN}← Good{RESET}")

        print(f"├─ Trade Size:    ${trade_size}")
        print(f"└─ Total Capital: ${trade_size * levels}\n")

        # Price in range?
        if current_price < lower:
            print(f"{RED}🚨 CRITICAL: Price ${current_price:,.2f} is BELOW grid range!{RESET}")
            print(f"{YELLOW}   Recommendation: Lower grid to {int(current_price * 0.95):,} - {int(current_price * 1.05):,}{RESET}\n")
        elif current_price > upper:
            print(f"{RED}🚨 CRITICAL: Price ${current_price:,.2f} is ABOVE grid range!{RESET}")
            print(f"{YELLOW}   Recommendation: Raise grid to {int(current_price * 0.95):,} - {int(current_price * 1.05):,}{RESET}\n")
        else:
            pct_in_range = ((current_price - lower) / (upper - lower)) * 100
            print(f"{GREEN}✓ Price is within grid range ({pct_in_range:.1f}% up from bottom){RESET}\n")

        # Next levels
        nearest_buy_idx = np.searchsorted(grids, current_price) - 1
        nearest_sell_idx = nearest_buy_idx + 1

        if 0 <= nearest_buy_idx < len(grids):
            nearest_buy = grids[nearest_buy_idx]
            distance_to_buy = current_price - nearest_buy
            trigger_threshold = grid_step * 0.5

            print(f"{BOLD}🎯 NEXT BUY SIGNAL{RESET}")
            print(f"├─ Nearest Buy Level:   ${nearest_buy:,.2f}")
            print(f"├─ Current Distance:    ${distance_to_buy:,.2f}")
            print(f"├─ Trigger Threshold:   ${trigger_threshold:,.2f}")

            if distance_to_buy < trigger_threshold:
                print(f"└─ Status: {GREEN}✓ IN BUY ZONE (should trigger soon){RESET}\n")
            else:
                drop_needed = distance_to_buy - trigger_threshold
                drop_pct = (drop_needed / current_price) * 100
                print(f"└─ Status: {RED}✗ Price needs to drop ${drop_needed:,.2f} ({drop_pct:.2f}%){RESET}\n")

        if 0 <= nearest_sell_idx < len(grids):
            nearest_sell = grids[nearest_sell_idx]
            distance_to_sell = nearest_sell - current_price
            sell_pct = (distance_to_sell / current_price) * 100

            print(f"{BOLD}💰 NEXT SELL SIGNAL{RESET}")
            print(f"├─ Nearest Sell Level:  ${nearest_sell:,.2f}")
            print(f"├─ Distance to Sell:    ${distance_to_sell:,.2f}")
            print(f"└─ Price needs to rise: {sell_pct:.2f}%\n")

        # Positions
        positions = self.get_open_positions(name)

        print(f"{BOLD}📦 POSITION STATUS{RESET}")
        if positions.empty:
            print(f"├─ Open Positions: {GREEN}0 - Ready to buy{RESET}")
            print(f"└─ Lock Status:    {GREEN}UNLOCKED{RESET}\n")
        else:
            print(f"├─ Open Positions: {YELLOW}{len(positions)}{RESET}")
            print(f"└─ Lock Status:    {RED}LOCKED (position prevents new buys){RESET}\n")

            for idx, pos in positions.iterrows():
                entry_price = float(pos['buy_price'])
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                pnl_usd = (current_price - entry_price) * float(pos['amount'])
                age = datetime.now() - pd.to_datetime(pos['buy_timestamp'])

                color = GREEN if pnl_pct > 0 else RED
                print(f"  Position #{pos['id']}: {pos['symbol']}")
                print(f"  ├─ Entry:  ${entry_price:,.2f}")
                print(f"  ├─ P&L:    {color}{pnl_pct:+.2f}% (${pnl_usd:+.2f}){RESET}")
                print(f"  └─ Age:    {age.days}d {age.seconds//3600}h\n")

        # Recommendations
        print(f"{BOLD}📈 RECOMMENDATIONS{RESET}")
        issues = []

        if grid_step > 500:
            issues.append(f"{RED}1. Grid step ${grid_step:,.0f} is TOO WIDE - reduce range or increase levels{RESET}")
            issues.append(f"   Suggested: Range ${int(current_price*0.95):,}-${int(current_price*1.05):,} with 40-50 levels")

        if current_price < lower or current_price > upper:
            issues.append(f"{RED}2. Price outside range - recenter grid around ${current_price:,.0f}{RESET}")

        if not positions.empty and len(positions) == 1:
            issues.append(f"{RED}3. Only 1 position open - bot is locked. Need to fix position lock in strategy code{RESET}")
            issues.append(f"   File: strategies/grid_strategy_v3.py - allow max_concurrent_positions=10")

        if levels < 30:
            issues.append(f"{YELLOW}4. Only {levels} grid levels - consider 40-50 for more opportunities{RESET}")

        if issues:
            for issue in issues:
                print(issue)
        else:
            print(f"{GREEN}✓ Configuration looks good!{RESET}")

        print()

    def diagnose_dip_bot(self, name, symbols, config):
        """Diagnose Buy-the-Dip bot"""
        print(f"{BOLD}{MAGENTA}{'='*100}{RESET}")
        print(f"{BOLD}{MAGENTA}📉 {name}{RESET}")
        print(f"{MAGENTA}{'='*100}{RESET}\n")

        dip_threshold = config.get('dip_threshold', 0.03)
        rsi_limit = config.get('rsi_limit', 35)

        print(f"{BOLD}⚙️  STRATEGY CONFIG{RESET}")
        print(f"├─ Dip Threshold:     {dip_threshold*100:.1f}% {RED if dip_threshold >= 0.03 else GREEN}{'← TOO HIGH' if dip_threshold >= 0.03 else '← Good'}{RESET}")
        print(f"├─ RSI Limit:         {rsi_limit}")
        print(f"├─ Trade Size:        ${config.get('amount', 15)}")
        print(f"├─ Max Per Coin:      ${config.get('max_exposure_per_coin', 100)}")
        print(f"└─ Take Profit:       {config.get('take_profit_pct', 0.08)*100:.1f}%\n")

        print(f"{BOLD}🔍 SCANNING TOP 10 COINS{RESET}\n")

        opportunities = []
        scan_results = []

        for symbol in symbols[:10]:
            df = self.get_price_data(symbol)

            if df is None or df.empty:
                scan_results.append((symbol, None, None, None, "Error"))
                continue

            current_price = float(df['close'].iloc[-1])
            high_24h = float(df['high'].max())
            rsi = calculate_rsi(df['close'].values)

            current_dip = (high_24h - current_price) / high_24h
            dip_ok = current_dip >= dip_threshold
            rsi_ok = rsi < rsi_limit

            scan_results.append((symbol, current_price, current_dip, rsi, "OK" if (dip_ok and rsi_ok) else "WAIT"))

            if dip_ok and rsi_ok:
                opportunities.append(symbol)

        # Display results
        for symbol, price, dip, rsi, status in scan_results:
            if price is None:
                print(f"{RED}✗ {symbol:12} | Error fetching data{RESET}")
                continue

            dip_pct = dip * 100
            dip_status = f"{GREEN}OK{RESET}" if dip >= dip_threshold else f"{RED}WAIT{RESET}"
            rsi_status = f"{GREEN}OK{RESET}" if rsi < rsi_limit else f"{RED}WAIT{RESET}"

            status_icon = f"{GREEN}✓{RESET}" if status == "OK" else f"{YELLOW}○{RESET}"

            print(f"{status_icon} {symbol:12} | ${price:>9.2f} | Dip: {dip_pct:>5.2f}% {dip_status} | RSI: {rsi:>5.1f} {rsi_status}")

        print()

        # Positions
        positions = self.get_open_positions(name)

        print(f"{BOLD}📦 CURRENT POSITIONS{RESET}")
        if positions.empty:
            print(f"{GREEN}└─ No open positions - ready to trade{RESET}\n")
        else:
            print(f"├─ Total Positions: {len(positions)}")
            total_exposure = sum(float(p['amount'] * p['buy_price']) for _, p in positions.iterrows())
            print(f"└─ Total Exposure:  ${total_exposure:,.2f}\n")

            for idx, pos in positions.iterrows():
                print(f"  • {pos['symbol']}: ${pos['buy_price']:.2f} x {pos['amount']}")

        print()

        print(f"{BOLD}📊 TRADING OPPORTUNITIES{RESET}")
        if opportunities:
            print(f"{GREEN}✓ {len(opportunities)} coins ready to buy NOW:{RESET}")
            for sym in opportunities:
                print(f"  • {sym}")
            print()
        else:
            print(f"{YELLOW}⚠ No coins meet both criteria{RESET}")
            print(f"  Need: Dip ≥ {dip_threshold*100:.1f}% AND RSI < {rsi_limit}\n")

        # Recommendations
        print(f"{BOLD}📈 RECOMMENDATIONS{RESET}")

        if dip_threshold >= 0.03:
            print(f"{RED}1. Lower dip threshold from {dip_threshold*100:.1f}% → 2.0% for more opportunities{RESET}")

        if not opportunities and positions.empty:
            print(f"{YELLOW}2. No positions and no opportunities - market is ranging. Consider 1.5% threshold.{RESET}")

        if len(opportunities) == 0 and dip_threshold < 0.03:
            print(f"{GREEN}✓ Threshold is reasonable. Market just hasn't dipped enough yet.{RESET}")

        print()

    def run(self):
        """Run full diagnostic"""
        print(f"\n{BOLD}{BLUE}{'='*100}{RESET}")
        print(f"{BOLD}{BLUE}🔬 CRYPTOBOT SIMPLE DIAGNOSTIC - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{BOLD}{BLUE}{'='*100}{RESET}\n")

        # Grid Bot BTC
        self.diagnose_grid_bot(
            "Grid Bot BTC",
            "BTC/USDT",
            {
                'lower_limit': 85000,
                'upper_limit': 110000,
                'grid_levels': 20,
                'amount': 25
            }
        )

        # Grid Bot ETH
        self.diagnose_grid_bot(
            "Grid Bot ETH",
            "ETH/USDT",
            {
                'lower_limit': 2800,
                'upper_limit': 4200,
                'grid_levels': 30,
                'amount': 25
            }
        )

        # Buy-the-Dip
        top_10 = [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT',
            'ADA/USDT', 'DOGE/USDT', 'TRX/USDT', 'DOT/USDT', 'LINK/USDT'
        ]

        self.diagnose_dip_bot(
            "Buy-the-Dip Strategy",
            top_10,
            {
                'dip_threshold': 0.03,
                'rsi_limit': 35,
                'amount': 15,
                'max_exposure_per_coin': 100,
                'take_profit_pct': 0.08
            }
        )

        print(f"{BOLD}{BLUE}{'='*100}{RESET}")
        print(f"{BOLD}{BLUE}✅ DIAGNOSTIC COMPLETE{RESET}")
        print(f"{BOLD}{BLUE}{'='*100}{RESET}\n")


if __name__ == "__main__":
    diagnostic = SimpleBotDiagnostic()
    diagnostic.run()
