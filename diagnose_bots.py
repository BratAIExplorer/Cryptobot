#!/usr/bin/env python3
"""
Real-Time Bot Diagnostic Tool
Shows exactly WHY bots are/aren't trading
"""

import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from utils.indicators import calculate_rsi, calculate_sma
import numpy as np

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
RESET = '\033[0m'
BOLD = '\033[1m'

class BotDiagnostic:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'data', 'multi', 'trades_paper.db')

        # Initialize exchange adapter
        self.exchange = None
        self._init_exchange()

    def _init_exchange(self):
        """Initialize Binance adapter"""
        try:
            # Try multiple import paths for different environments
            try:
                from adapters.binance_adapter import BinanceAdapter
            except ImportError:
                from core.adapters.binance_adapter import BinanceAdapter

            self.exchange = BinanceAdapter(mode='paper')
            print(f"{GREEN}✓ Exchange adapter initialized{RESET}\n")
        except Exception as e:
            print(f"{RED}✗ Failed to initialize exchange: {e}{RESET}")
            print(f"{YELLOW}  Running in DB-only mode (no live price data){RESET}\n")

    def check_db_schema(self):
        """Check and display database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            schema_info = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                schema_info[table] = columns

            conn.close()
            return schema_info
        except Exception as e:
            print(f"{RED}✗ Error reading schema: {e}{RESET}")
            return {}

    def get_open_positions(self, bot_name=None):
        """Get open positions from database"""
        try:
            conn = sqlite3.connect(self.db_path)

            # First, check what columns exist
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(positions)")
            columns = [row[1] for row in cursor.fetchall()]

            # Adapt query based on available columns
            # V3 uses 'price' instead of 'buy_price', 'timestamp' instead of 'buy_timestamp'
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
        """Diagnose Grid Bot trading status"""
        print(f"{BOLD}{CYAN}{'='*100}{RESET}")
        print(f"{BOLD}{CYAN}🤖 {name} - {symbol}{RESET}")
        print(f"{CYAN}{'='*100}{RESET}\n")

        # Get current price
        if self.exchange:
            df = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
            if df.empty:
                print(f"{RED}✗ Cannot fetch price data{RESET}\n")
                return
            current_price = float(df['close'].iloc[-1])
            rsi = float(calculate_rsi(df['close']).iloc[-1])
        else:
            print(f"{YELLOW}⚠ No exchange connection - using placeholder prices{RESET}\n")
            return

        # Grid Configuration
        lower = config['lower_limit']
        upper = config['upper_limit']
        levels = config['grid_levels']
        trade_size = config['amount']

        # Calculate grid
        grids = np.linspace(lower, upper, levels)
        grid_step = (upper - lower) / (levels - 1)

        print(f"{BOLD}📊 MARKET STATUS{RESET}")
        print(f"├─ Current Price: ${current_price:,.2f}")
        print(f"├─ RSI (14):      {rsi:.1f}")
        print(f"├─ 24h High:      ${float(df['high'].max()):,.2f}")
        print(f"├─ 24h Low:       ${float(df['low'].min()):,.2f}")
        print(f"└─ 24h Range:     ${float(df['high'].max() - df['low'].min()):,.2f}\n")

        print(f"{BOLD}⚙️  GRID CONFIGURATION{RESET}")
        print(f"├─ Range:         ${lower:,} - ${upper:,} ({YELLOW}${upper-lower:,} spread{RESET})")
        print(f"├─ Grid Levels:   {levels}")
        print(f"├─ Grid Step:     ${grid_step:,.2f} {RED}← TOO WIDE{RESET}" if grid_step > 500 else f"├─ Grid Step:     ${grid_step:,.2f}")
        print(f"├─ Trade Size:    ${trade_size}")
        print(f"└─ Total Capital: ${trade_size * levels}\n")

        # Check if price is in range
        if current_price < lower or current_price > upper:
            print(f"{RED}🚨 CRITICAL: Price ${current_price:,.2f} is OUTSIDE grid range!{RESET}")
            print(f"{YELLOW}   Action: Adjust range to {int(current_price * 0.95):,} - {int(current_price * 1.05):,}{RESET}\n")
        else:
            print(f"{GREEN}✓ Price is within grid range{RESET}\n")

        # Find nearest grid levels
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
                print(f"└─ Status: {GREEN}✓ WITHIN BUY ZONE{RESET}\n")
            else:
                print(f"└─ Status: {RED}✗ TOO FAR - Needs ${distance_to_buy - trigger_threshold:,.2f} drop{RESET}\n")

        if 0 <= nearest_sell_idx < len(grids):
            nearest_sell = grids[nearest_sell_idx]
            distance_to_sell = nearest_sell - current_price

            print(f"{BOLD}💰 NEXT SELL SIGNAL{RESET}")
            print(f"├─ Nearest Sell Level:  ${nearest_sell:,.2f}")
            print(f"├─ Distance to Sell:    ${distance_to_sell:,.2f}")
            print(f"└─ Price needs to rise: {(distance_to_sell/current_price)*100:.2f}%\n")

        # Check positions
        positions = self.get_open_positions(name)

        print(f"{BOLD}📦 POSITION STATUS{RESET}")
        if positions.empty:
            print(f"├─ Open Positions: {GREEN}0 - Ready to buy{RESET}")
            print(f"└─ Lock Status:    {GREEN}UNLOCKED{RESET}\n")
        else:
            print(f"├─ Open Positions: {YELLOW}{len(positions)}{RESET}")
            print(f"└─ Lock Status:    {RED}LOCKED (can't buy more until sell){RESET}\n")

            for idx, pos in positions.iterrows():
                entry_price = float(pos['buy_price'])
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                pnl_usd = (current_price - entry_price) * float(pos['amount'])
                age = datetime.now() - pd.to_datetime(pos['buy_timestamp'])

                print(f"  Position #{pos['id']}")
                print(f"  ├─ Entry:  ${entry_price:,.2f}")
                print(f"  ├─ P&L:    {GREEN if pnl_pct > 0 else RED}{pnl_pct:+.2f}% (${pnl_usd:+.2f}){RESET}")
                print(f"  └─ Age:    {age.days}d {age.seconds//3600}h\n")

        # Trading Activity
        print(f"{BOLD}📈 TRADING RECOMMENDATIONS{RESET}")

        issues = []
        if grid_step > 500:
            issues.append(f"Grid step ${grid_step:,.0f} is TOO WIDE - reduce to $100-250")
        if current_price < lower or current_price > upper:
            issues.append(f"Price outside range - recenter grid around ${current_price:,.0f}")
        if not positions.empty:
            issues.append("Position lock active - modify strategy to allow multiple positions")
        if levels < 30:
            issues.append(f"Only {levels} grid levels - increase to 40-50 for more opportunities")

        if issues:
            for i, issue in enumerate(issues, 1):
                print(f"{RED}{i}. {issue}{RESET}")
        else:
            print(f"{GREEN}✓ Configuration looks good{RESET}")

        print()

    def diagnose_dip_bot(self, name, symbols, config):
        """Diagnose Buy-the-Dip bot"""
        print(f"{BOLD}{MAGENTA}{'='*100}{RESET}")
        print(f"{BOLD}{MAGENTA}📉 {name}{RESET}")
        print(f"{MAGENTA}{'='*100}{RESET}\n")

        dip_threshold = config.get('dip_threshold', 0.03)
        rsi_limit = config.get('rsi_limit', 35)

        print(f"{BOLD}⚙️  STRATEGY CONFIG{RESET}")
        print(f"├─ Dip Threshold:     {dip_threshold*100:.1f}%")
        print(f"├─ RSI Limit:         {rsi_limit}")
        print(f"├─ Trade Size:        ${config.get('amount', 15)}")
        print(f"├─ Max Per Coin:      ${config.get('max_exposure_per_coin', 100)}")
        print(f"└─ Take Profit:       {config.get('take_profit_pct', 0.08)*100:.1f}%\n")

        # Check each symbol
        print(f"{BOLD}🔍 SCANNING {len(symbols)} COINS{RESET}\n")

        opportunities = []

        for symbol in symbols[:5]:  # Check first 5 to avoid rate limits
            try:
                if not self.exchange:
                    print(f"{YELLOW}⚠ No exchange connection{RESET}")
                    break

                df = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                if df.empty:
                    continue

                current_price = float(df['close'].iloc[-1])
                high_24h = float(df['high'].max())
                low_24h = float(df['low'].min())
                rsi = float(calculate_rsi(df['close']).iloc[-1])

                # Calculate dip
                current_dip = (high_24h - current_price) / high_24h

                # Check conditions
                dip_ok = current_dip >= dip_threshold
                rsi_ok = rsi < rsi_limit

                status_icon = f"{GREEN}✓{RESET}" if (dip_ok and rsi_ok) else f"{RED}✗{RESET}"

                print(f"{status_icon} {symbol:12} | Price: ${current_price:>8.2f} | Dip: {current_dip*100:>5.2f}% {GREEN if dip_ok else RED}{'OK' if dip_ok else 'WAIT'}{RESET} | RSI: {rsi:>5.1f} {GREEN if rsi_ok else RED}{'OK' if rsi_ok else 'WAIT'}{RESET}")

                if dip_ok and rsi_ok:
                    opportunities.append(symbol)

            except Exception as e:
                print(f"{RED}✗ {symbol:12} | Error: {e}{RESET}")

        print()

        # Check positions
        positions = self.get_open_positions(name)

        print(f"{BOLD}📦 CURRENT POSITIONS{RESET}")
        if positions.empty:
            print(f"{GREEN}└─ No open positions{RESET}\n")
        else:
            print(f"├─ Total Positions: {len(positions)}")
            print(f"└─ Total Exposure:  ${float(positions['amount'].sum() * positions['buy_price'].mean()):,.2f}\n")

        print(f"{BOLD}📊 TRADING OPPORTUNITIES{RESET}")
        if opportunities:
            print(f"{GREEN}✓ {len(opportunities)} coins ready to buy:{RESET}")
            for sym in opportunities:
                print(f"  • {sym}")
        else:
            print(f"{YELLOW}⚠ No coins meet criteria currently{RESET}")
            print(f"{YELLOW}  Either dip < {dip_threshold*100:.1f}% or RSI > {rsi_limit}{RESET}")

        print()

        print(f"{BOLD}📈 RECOMMENDATIONS{RESET}")
        issues = []

        if dip_threshold >= 0.03:
            issues.append(f"Dip threshold {dip_threshold*100:.1f}% is too conservative - try 2.0% for ranging markets")

        if not opportunities and not positions.empty:
            issues.append("Positions stuck - no new opportunities. Consider lowering thresholds.")

        if issues:
            for i, issue in enumerate(issues, 1):
                print(f"{RED}{i}. {issue}{RESET}")
        else:
            print(f"{GREEN}✓ Strategy parameters look reasonable{RESET}")

        print()

    def run_full_diagnostic(self):
        """Run complete diagnostic on all bots"""
        print(f"\n{BOLD}{BLUE}{'='*100}{RESET}")
        print(f"{BOLD}{BLUE}🔬 CRYPTOBOT DIAGNOSTIC TOOL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{BOLD}{BLUE}{'='*100}{RESET}\n")

        print(f"{BOLD}📁 DATABASE{RESET}")
        print(f"├─ Path: {self.db_path}")
        if os.path.exists(self.db_path):
            size_mb = os.path.getsize(self.db_path) / (1024*1024)
            print(f"└─ Size: {size_mb:.2f} MB {GREEN}✓ EXISTS{RESET}")

            # Show schema info
            schema = self.check_db_schema()
            if schema:
                print(f"\n{BOLD}📊 DATABASE SCHEMA{RESET}")
                for table, cols in schema.items():
                    print(f"├─ {table}: {', '.join(cols[:5])}{'...' if len(cols) > 5 else ''}")
                print()
        else:
            print(f"{RED}└─ ✗ DATABASE NOT FOUND{RESET}\n")
            return

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
    diagnostic = BotDiagnostic()
    diagnostic.run_full_diagnostic()
