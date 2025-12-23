"""
CryptoIntel Hub - Coin Configuration
Customizable multi-coin support for decision engine
"""

# Tracked Coins Configuration
# Add or remove coins here - the entire system adapts automatically
TRACKED_COINS = {
    'XRP': {
        'name': 'Ripple',
        'category': 'Payment',
        'priority': 'HIGH',  # HIGH/MEDIUM/LOW
        'min_position_size': 100,  # Min USD allocation
        'max_position_size': 5000,  # Max USD allocation
        'enabled': True
    },
    'BTC': {
        'name': 'Bitcoin',
        'category': 'Store of Value',
        'priority': 'HIGH',
        'min_position_size': 500,
        'max_position_size': 10000,
        'enabled': True
    },
    'ETH': {
        'name': 'Ethereum',
        'category': 'Smart Contract Platform',
        'priority': 'HIGH',
        'min_position_size': 200,
        'max_position_size': 7000,
        'enabled': True
    },
    'XLM': {
        'name': 'Stellar',
        'category': 'Payment',
        'priority': 'MEDIUM',
        'min_position_size': 100,
        'max_position_size': 3000,
        'enabled': True
    },
    'ADA': {
        'name': 'Cardano',
        'category': 'Smart Contract Platform',
        'priority': 'MEDIUM',
        'min_position_size': 100,
        'max_position_size': 4000,
        'enabled': True
    },
    'SOL': {
        'name': 'Solana',
        'category': 'Smart Contract Platform',
        'priority': 'HIGH',
        'min_position_size': 200,
        'max_position_size': 5000,
        'enabled': True
    }
}

# Confluence Score Weights (Total = 100 points)
CONFLUENCE_WEIGHTS = {
    'technical': 30,      # RSI, MA, MACD, Volume
    'onchain': 30,        # Whale holdings, exchange reserves, velocity
    'macro': 20,          # BTC correlation, risk regime, Fed rates
    'fundamental': 20     # ETF flows, sector rotation, model forecast
}

# Position Sizing Thresholds
POSITION_RECOMMENDATIONS = {
    'STRONG_BUY': {
        'min_score': 80,
        'position_size': '8-10%',
        'stop_loss_pct': 15,
        'color': 'green'
    },
    'CAUTIOUS_BUY': {
        'min_score': 60,
        'position_size': '5-7%',
        'stop_loss_pct': 10,
        'color': 'yellow'
    },
    'HOLD_WAIT': {
        'min_score': 40,
        'position_size': '2-4%',
        'stop_loss_pct': 7,
        'color': 'orange'
    },
    'AVOID': {
        'min_score': 0,
        'position_size': '0-1%',
        'stop_loss_pct': 5,
        'color': 'red'
    }
}

# Model Validation Thresholds
MODEL_HEALTH_CRITERIA = {
    'EXCELLENT': {
        'min_win_rate': 0.60,
        'max_mape': 0.15,
        'min_sharpe': 1.5
    },
    'GOOD': {
        'min_win_rate': 0.50,
        'max_mape': 0.25,
        'min_sharpe': 1.0
    },
    'FAIR': {
        'min_win_rate': 0.40,
        'max_mape': 0.35,
        'min_sharpe': 0.5
    }
    # Anything below FAIR = POOR (do not trade)
}

# API Configuration (Free Tier)
API_CONFIG = {
    'coinglass': {
        'enabled': True,
        'rate_limit': 100,  # requests per day
        'cache_ttl': 86400  # 24 hours
    },
    'coingecko': {
        'enabled': True,
        'rate_limit': 50,   # requests per minute
        'cache_ttl': 300    # 5 minutes
    },
    'glassnode': {
        'enabled': False,   # Set to True when subscribed
        'tier': 'FREE',     # FREE/BASIC/STANDARD/ADVANCED
        'rate_limit': 10    # Free tier limit
    }
}

def get_enabled_coins():
    """Get list of enabled coin symbols"""
    return [symbol for symbol, config in TRACKED_COINS.items() if config['enabled']]

def get_coin_config(symbol):
    """Get configuration for specific coin"""
    return TRACKED_COINS.get(symbol, None)

def get_position_recommendation(score):
    """Get position recommendation based on confluence score"""
    for category, config in sorted(POSITION_RECOMMENDATIONS.items(), 
                                   key=lambda x: x[1]['min_score'], 
                                   reverse=True):
        if score >= config['min_score']:
            return {
                'rating': category.replace('_', ' '),
                'position_size': config['position_size'],
                'stop_loss_pct': config['stop_loss_pct'],
                'color': config['color']
            }
    return POSITION_RECOMMENDATIONS['AVOID']

# Discovery Watchlist for Scanner
DISCOVERY_WATCHLIST = [
    'SOL/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'POL/USDT', 
    'ATOM/USDT', 'NEAR/USDT', 'ALGO/USDT', 'FIL/USDT', 'HBAR/USDT',
    'AVAX/USDT', 'LTC/USDT', 'UNI/USDT', 'ICP/USDT', 'AAVE/USDT'
]

# Sector Mapping for Fundamental Proxy
SECTOR_MAPPING = {
    'Payment': ['XRP', 'XLM', 'LTC', 'BCH'],
    'Smart Contract': ['ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'NEAR', 'MATIC', 'ATOM', 'ALGO'],
    'DeFi': ['UNI', 'LINK', 'AAVE', 'ICP'],
    'Storage': ['FIL'],
    'Enterprise': ['VET', 'HBAR']
}

def classify_model_health(win_rate, mape, sharpe_ratio):
    """Classify model health based on metrics"""
    for category, criteria in MODEL_HEALTH_CRITERIA.items():
        if (win_rate >= criteria['min_win_rate'] and 
            mape <= criteria['max_mape'] and 
            sharpe_ratio >= criteria['min_sharpe']):
            return category
    return 'POOR'
