#!/usr/bin/env python3
"""
Binance Grid Trading Bot - Paper & Live Trading
Supports testnet (paper) and live trading with capital controls
"""
import os
import sys
import time
import ccxt
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
class Config:
    # Trading mode: 'paper' or 'live'
    TRADING_MODE = os.getenv('TRADING_MODE', 'paper')

    # Exchange
    EXCHANGE = 'binance'

    # Sandbox mode (testnet)
    SANDBOX_MODE = (TRADING_MODE == 'paper')

    # Load API credentials based on mode
    if TRADING_MODE == 'paper':
        env_file = '.env.binance.paper'
    else:
        env_file = '.env.binance.live'

    # Load environment
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip()

    # API Keys
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET = os.getenv('BINANCE_SECRET')

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    # Capital Allocation
    ALLOCATION_BTC = 80  # USD
    ALLOCATION_ETH = 60  # USD
    TOTAL_ALLOCATION = ALLOCATION_BTC + ALLOCATION_ETH  # 140 USD

    # Grid Settings
    GRID_LEVELS = 5
    BTC_RANGE_PCT = 0.08  # 8% range
    ETH_RANGE_PCT = 0.10  # 10% range

    # Risk Management
    DAILY_LOSS_LIMIT = 50  # USD

    # Logging
    LOG_FILE = 'logs/bot_binance_grid.log'

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Simple Telegram notifier"""
    def __init__(self, token: str, chat_id: str, mode: str = 'paper'):
        self.token = token
        self.chat_id = chat_id
        self.mode = mode.lower()
        self.is_live = (self.mode == 'live')

    def send_message(self, message: str):
        """Send Telegram message with mode indicator"""
        if not self.token or not self.chat_id:
            return

        try:
            import requests

            # Add mode prefix
            if self.is_live:
                prefix = "🔴 LIVE\n"
                suffix = "\n\n⚠️ Real money trade"
            else:
                prefix = "📝 PAPER\n"
                suffix = "\n\n(Testnet - fake money)"

            full_message = f"{prefix}{message}{suffix}"

            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': full_message,
                'parse_mode': 'HTML'
            }
            requests.post(url, data=data, timeout=5)
        except Exception as e:
            logger.warning(f"Telegram notification failed: {e}")

class GridBot:
    """Grid Trading Bot for Binance"""

    def __init__(self, symbol: str, allocation: float, range_pct: float):
        self.symbol = symbol
        self.allocation = allocation
        self.range_pct = range_pct
        self.grid_levels = Config.GRID_LEVELS

        # Initialize exchange
        self.exchange = self._init_exchange()

        # State tracking
        self.grids: List[Dict] = []
        self.open_orders: List[Dict] = []
        self.positions: List[Dict] = []
        self.total_spent = 0
        self.total_sold = 0

        logger.info(f"Initialized GridBot for {symbol}")
        logger.info(f"  Allocation: ${allocation}")
        logger.info(f"  Range: {range_pct*100}%")
        logger.info(f"  Grid Levels: {self.grid_levels}")
        logger.info(f"  Mode: {Config.TRADING_MODE.upper()}")
        logger.info(f"  Sandbox: {Config.SANDBOX_MODE}")

    def _init_exchange(self):
        """Initialize Binance exchange"""
        try:
            exchange = ccxt.binance({
                'apiKey': Config.BINANCE_API_KEY,
                'secret': Config.BINANCE_SECRET,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            })

            # Enable sandbox mode for testnet/paper trading
            if Config.SANDBOX_MODE:
                exchange.set_sandbox_mode(True)
                logger.info("Sandbox mode enabled (testnet)")
            else:
                logger.info("Live trading mode (production)")

            return exchange

        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise

    def get_current_price(self) -> float:
        """Get current market price"""
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Failed to fetch price for {self.symbol}: {e}")
            return None

    def calculate_grids(self, current_price: float) -> List[Dict]:
        """Calculate grid levels based on current price"""
        # Calculate price range
        lower_bound = current_price * (1 - self.range_pct / 2)
        upper_bound = current_price * (1 + self.range_pct / 2)
        step = (upper_bound - lower_bound) / self.grid_levels

        grids = []
        allocation_per_level = self.allocation / self.grid_levels

        for i in range(self.grid_levels):
            price = lower_bound + (step * i)

            # Determine if buy or sell based on position relative to current price
            if price < current_price:
                order_type = 'buy'
                # Amount in base currency (BTC/ETH)
                amount = allocation_per_level / price
            else:
                order_type = 'sell'
                amount = allocation_per_level / current_price

            grids.append({
                'level': i,
                'price': round(price, 2),
                'type': order_type,
                'amount': amount,
                'allocation': allocation_per_level
            })

        return grids

    def check_available_capital(self) -> float:
        """Check how much capital is available (not locked in orders)"""
        return self.allocation - self.total_spent

    def place_grid_orders(self):
        """Calculate and display grid orders (paper mode) or place real orders (live mode)"""
        try:
            current_price = self.get_current_price()
            if not current_price:
                logger.error("Cannot place orders without current price")
                return

            logger.info(f"\n{'='*60}")
            logger.info(f"Grid Calculation for {self.symbol}")
            logger.info(f"Current Price: ${current_price:,.2f}")
            logger.info(f"Allocation: ${self.allocation:,.2f}")
            logger.info(f"Range: ±{self.range_pct*100/2:.1f}%")
            logger.info(f"{'='*60}\n")

            # Calculate grids
            self.grids = self.calculate_grids(current_price)

            # Display/place each grid level
            for grid in self.grids:
                level = grid['level']
                price = grid['price']
                order_type = grid['type']
                amount = grid['amount']
                allocation = grid['allocation']

                # Calculate price difference from current
                diff_pct = ((price - current_price) / current_price) * 100

                logger.info(f"Level {level}: {order_type.upper()}")
                logger.info(f"  Price: ${price:,.2f} ({diff_pct:+.2f}% from current)")
                logger.info(f"  Amount: {amount:.8f} {self.symbol.split('/')[0]}")
                logger.info(f"  Value: ${allocation:,.2f}")

                if Config.TRADING_MODE == 'live' and not Config.SANDBOX_MODE:
                    # TODO: Place real orders in live mode
                    # For now, just log
                    logger.info(f"  [LIVE] Would place order here")
                else:
                    logger.info(f"  [PAPER] Simulated order")

                logger.info("")

            # Summary
            total_buy_value = sum(g['allocation'] for g in self.grids if g['type'] == 'buy')
            total_sell_value = sum(g['allocation'] for g in self.grids if g['type'] == 'sell')

            logger.info(f"Grid Summary:")
            logger.info(f"  Buy Levels: ${total_buy_value:,.2f}")
            logger.info(f"  Sell Levels: ${total_sell_value:,.2f}")
            logger.info(f"  Total: ${total_buy_value + total_sell_value:,.2f}")
            logger.info(f"  Available Capital: ${self.check_available_capital():,.2f}")

        except Exception as e:
            logger.error(f"Error placing grid orders: {e}")
            import traceback
            traceback.print_exc()

    def monitor_and_update(self):
        """Monitor positions and update grids if needed"""
        try:
            current_price = self.get_current_price()
            if not current_price:
                return

            logger.info(f"[{self.symbol}] Current: ${current_price:,.2f} | "
                       f"Spent: ${self.total_spent:,.2f}/{self.allocation:,.2f}")

            # In live mode, would check for filled orders and update grids
            # For paper mode, just monitor

        except Exception as e:
            logger.error(f"Error monitoring {self.symbol}: {e}")

class MultiGridBot:
    """Manages multiple Grid bots (BTC + ETH)"""

    def __init__(self):
        self.notifier = None
        if Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHAT_ID:
            self.notifier = TelegramNotifier(
                Config.TELEGRAM_BOT_TOKEN,
                Config.TELEGRAM_CHAT_ID,
                Config.TRADING_MODE
            )

        # Initialize bots
        self.bots: Dict[str, GridBot] = {}

        logger.info(f"\n{'='*80}")
        logger.info(f"BINANCE GRID BOT - {Config.TRADING_MODE.upper()} MODE")
        logger.info(f"{'='*80}\n")

        # Send startup notification
        if self.notifier:
            mode_emoji = "🔴" if Config.TRADING_MODE == 'live' else "📝"
            msg = f"{mode_emoji} Grid Bot Starting\n"
            msg += f"Mode: {Config.TRADING_MODE.upper()}\n"
            msg += f"BTC Allocation: ${Config.ALLOCATION_BTC}\n"
            msg += f"ETH Allocation: ${Config.ALLOCATION_ETH}\n"
            msg += f"Total: ${Config.TOTAL_ALLOCATION}"
            self.notifier.send_message(msg)

    def add_bot(self, symbol: str, allocation: float, range_pct: float):
        """Add a Grid bot for a symbol"""
        bot = GridBot(symbol, allocation, range_pct)
        self.bots[symbol] = bot
        return bot

    def run(self):
        """Main run loop"""
        try:
            # Add bots
            logger.info("Setting up Grid bots...")
            self.add_bot('BTC/USDT', Config.ALLOCATION_BTC, Config.BTC_RANGE_PCT)
            self.add_bot('ETH/USDT', Config.ALLOCATION_ETH, Config.ETH_RANGE_PCT)

            # Initial grid calculation
            logger.info("\nCalculating initial grids...")
            for symbol, bot in self.bots.items():
                bot.place_grid_orders()

            # Monitor loop
            logger.info(f"\n{'='*80}")
            logger.info("Starting monitoring loop (Ctrl+C to stop)...")
            logger.info(f"{'='*80}\n")

            cycle = 0
            while True:
                cycle += 1
                logger.info(f"\n--- Cycle {cycle} ({datetime.now().strftime('%H:%M:%S')}) ---")

                # Monitor each bot
                for symbol, bot in self.bots.items():
                    bot.monitor_and_update()

                # Wait before next cycle
                logger.info(f"Waiting 60 seconds until next cycle...\n")
                time.sleep(60)

        except KeyboardInterrupt:
            logger.info("\n\nShutdown requested by user (Ctrl+C)")
            if self.notifier:
                self.notifier.send_message("Grid Bot stopped by user")

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
            if self.notifier:
                self.notifier.send_message(f"Grid Bot ERROR: {e}")

        finally:
            logger.info("Grid Bot shutdown complete")

def main():
    """Main entry point"""
    # Validate configuration
    if not Config.BINANCE_API_KEY or not Config.BINANCE_SECRET:
        print("ERROR: BINANCE_API_KEY and BINANCE_SECRET must be set")
        print(f"Please configure {Config.env_file}")
        sys.exit(1)

    # Check mode
    logger.info(f"Starting in {Config.TRADING_MODE.upper()} mode")
    if Config.SANDBOX_MODE:
        logger.info("Using Binance TESTNET (fake money)")
    else:
        logger.info("Using Binance LIVE (REAL MONEY!)")

        # Safety confirmation for live mode
        if Config.TRADING_MODE == 'live':
            print("\n" + "="*80)
            print("⚠️  WARNING: LIVE TRADING MODE ⚠️")
            print("="*80)
            print("You are about to trade with REAL MONEY on Binance")
            print(f"Allocated Capital: ${Config.TOTAL_ALLOCATION}")
            print("\nType 'YES' to confirm, or Ctrl+C to abort:")

            confirmation = input().strip()
            if confirmation != 'YES':
                print("Aborted by user")
                sys.exit(0)

    # Run bot
    bot = MultiGridBot()
    bot.run()

if __name__ == '__main__':
    main()
