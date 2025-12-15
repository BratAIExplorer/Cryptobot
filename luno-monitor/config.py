"""
Configuration module for Luno Portfolio Monitor
Loads environment variables and defines application settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Luno API Configuration (READ-ONLY)
LUNO_API_KEY_ID = os.getenv('LUNO_API_KEY_ID')
LUNO_API_KEY_SECRET = os.getenv('LUNO_API_KEY_SECRET')
LUNO_BASE_URL = 'https://api.luno.com/api/1'

# Gmail Configuration
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Profit Targets (percentages)
PROFIT_TARGETS = [float(x.strip()) for x in os.getenv('PROFIT_TARGETS', '20,35,50').split(',')]

# Alert Preferences
ENABLE_DESKTOP_NOTIFICATIONS = os.getenv('ENABLE_DESKTOP_NOTIFICATIONS', 'true').lower() == 'true'
ENABLE_EMAIL_ALERTS = os.getenv('ENABLE_EMAIL_ALERTS', 'true').lower() == 'true'
ENABLE_TELEGRAM_ALERTS = os.getenv('ENABLE_TELEGRAM_ALERTS', 'true').lower() == 'true'

# Monitoring Settings
PRICE_CHECK_INTERVAL_SECONDS = int(os.getenv('PRICE_CHECK_INTERVAL_SECONDS', '1800'))  # Check every 30 minutes
ALERT_ON_PRICE_DROP_PERCENT = float(os.getenv('ALERT_ON_PRICE_DROP_PERCENT', '5'))

# Dashboard Settings
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '5000'))
DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', 'localhost')

# Cryptocurrency pairs on Luno
# NOTE: Using MYR (Malaysian Ringgit) pairs for Malaysia region
CRYPTO_PAIRS = {
    'BTC': 'XBTMYR',   # Bitcoin
    'XRP': 'XRPMYR',   # Ripple
    'POL': 'POLMYR',   # Polygon (formerly MATIC)
    'LINK': 'LINKMYR', # Chainlink
    'ALGO': 'ALGOMYR', # Algorand
    'XLM': 'XLMMYR',   # Stellar
    'SNX': 'SNXMYR',   # Synthetix
    'GRT': 'GRTMYR',   # The Graph
    'ETH': 'ETHMYR',   # Ethereum
    'ADA': 'ADAMYR',   # Cardano
    'NEAR': 'NEARMYR'  # NEAR Protocol
}

# CoinGecko API IDs for price fallback
COINGECKO_IDS = {
    'BTC': 'bitcoin',
    'XRP': 'ripple',
    'POL': 'polygon-ecosystem-token',
    'LINK': 'chainlink',
    'ALGO': 'algorand',
    'XLM': 'stellar',
    'SNX': 'synthetix-network-token',
    'GRT': 'the-graph',
    'ETH': 'ethereum',
    'ADA': 'cardano',
    'NEAR': 'near'
}

# Luno Fee Structure (approximate - will be fetched via API)
# Maker/Taker fees vary by volume, typical range:
ESTIMATED_MAKER_FEE = 0.001  # 0.1%
ESTIMATED_TAKER_FEE = 0.0025 # 0.25%

# Currency Display Settings
DISPLAY_CURRENCY = 'MYR'  # Malaysian Ringgit
BASE_CURRENCY = 'MYR'     # Luno API returns MYR (Malaysian market)

def validate_config():
    """Validate that all required configuration is present"""
    errors = []
    
    if not LUNO_API_KEY_ID:
        errors.append("LUNO_API_KEY_ID is not set")
    if not LUNO_API_KEY_SECRET:
        errors.append("LUNO_API_KEY_SECRET is not set")
    
    if ENABLE_EMAIL_ALERTS:
        if not GMAIL_ADDRESS:
            errors.append("GMAIL_ADDRESS is required for email alerts")
        if not GMAIL_APP_PASSWORD:
            errors.append("GMAIL_APP_PASSWORD is required for email alerts")
    
    if ENABLE_TELEGRAM_ALERTS:
        if not TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required for Telegram alerts")
        if not TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID is required for Telegram alerts")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True

if __name__ == "__main__":
    # Test configuration
    try:
        validate_config()
        print("✓ Configuration is valid")
        print(f"✓ Monitoring {len(CRYPTO_PAIRS)} cryptocurrencies")
        print(f"✓ Profit targets: {PROFIT_TARGETS}%")
    except ValueError as e:
        print(f"✗ {e}")
