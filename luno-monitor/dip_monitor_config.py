"""
Dip Monitor Configuration
Tracks price drops for buying opportunities
"""

# Coins to monitor for dip buying opportunities
# Format: 'SYMBOL': {'pair': 'LUNO_PAIR', 'tier1_drop': %, 'tier2_drop': %}
DIP_WATCH_LIST = {
    'SOL': {
        'pair': 'SOLMYR',
        'name': 'Solana',
        'tier1_drop': 10,  # Alert at 10% drop (first buying opportunity)
        'tier2_drop': 20,  # Alert at 20% drop (deep dip buying)
        'baseline_price': 511.00  # Current price as baseline (will auto-update)
    },
    'LINK': {
        'pair': 'LINKMYR', 
        'name': 'Chainlink',
        'tier1_drop': 10,
        'tier2_drop': 20,
        'baseline_price': 49.21
    },
    'POL': {
        'pair': 'POLMYR',
        'name': 'Polygon',
        'tier1_drop': 10,
        'tier2_drop': 20,
        'baseline_price': 0.49
    },
    'ETH': {
        'pair': 'ETHMYR',
        'name': 'Ethereum',
        'tier1_drop': 10,
        'tier2_drop': 20,
        'baseline_price': 11308.00
    },
    'AVAX': {
        'pair': 'AVAXMYR',
        'name': 'Avalanche',
        'tier1_drop': 15,  # Slightly higher threshold (more volatile)
        'tier2_drop': 25,
        'baseline_price': 52.23
    }
}

# Alert cooldown (minutes) - prevent spam if price oscillates
ALERT_COOLDOWN_MINUTES = 120  # 2 hours between alerts for same coin

# How often to check prices (seconds)
CHECK_INTERVAL_SECONDS = 1800  # Every 30 minutes

# Monitor duration (days)
MONITOR_DURATION_DAYS = 30

# Use 24-hour high as baseline (auto-updates)
USE_24H_HIGH_BASELINE = True

# Baseline update frequency (hours)
BASELINE_UPDATE_HOURS = 24
