"""
Configuration for Multi-Asset Intelligence System

Feature flags control system activation. All OFF by default for safety.
"""

# ==========================================
# Feature Flags (Control Integration)
# ==========================================

FEATURE_FLAGS = {
    # Manual scoring tools
    'use_regulatory_scorer': False,  # OFF by default
    'use_master_decision': False,    # OFF by default
    
    # Bot integration (Phase 9 - Future)
    'enhance_bots': False,           # OFF by default
    'enhanced_bots': [],             # List of bot names to enhance
}

# ==========================================
# Asset Type Mappings
# ==========================================

# Type A: Technical Assets (Use Confluence V2)
TECHNICAL_ASSETS = {
    'BTC/USDT': {'reason': 'Pure technical/macro driven', 'scorer': 'confluence_v2'},
    'ETH/USDT': {'reason': 'Mostly technical driven', 'scorer': 'confluence_v2'},
    'DOGE/USDT': {'reason': 'Speculation/technical', 'scorer': 'confluence_v2'},
    'LTC/USDT': {'reason': 'Technical patterns', 'scorer': 'confluence_v2'},
    'BCH/USDT': {'reason': 'Technical patterns', 'scorer': 'confluence_v2'},
}

# Type B: Regulatory/Fundamental Assets (Use Regulatory Scorer)
REGULATORY_ASSETS = {
    'XRP/USDT': {
        'reason': 'SEC lawsuit, ETFs, institutional adoption',
        'scorer': 'regulatory',
        'key_metrics': ['regulatory_progress', 'institutional_adoption', 'partnerships']
    },
    'ADA/USDT': {
        'reason': 'Government contracts, academic partnerships',
        'scorer': 'regulatory',
        'key_metrics': ['development_milestones', 'partnerships', 'ecosystem_growth']
    },
    'SOL/USDT': {
        'reason': 'Institutional VCs, ecosystem growth, network reliability',
        'scorer': 'regulatory',
        'key_metrics': ['institutional_backing', 'ecosystem_metrics', 'network_uptime']
    },
    'MATIC/USDT': {
        'reason': 'Enterprise adoption (Disney, Starbucks, Reddit)',
        'scorer': 'regulatory',
        'key_metrics': ['enterprise_partnerships', 'zk_development', 'migration_progress']
    },
    'LINK/USDT': {
        'reason': 'Banking integrations (SWIFT), oracle adoption',
        'scorer': 'regulatory',
        'key_metrics': ['partnerships', 'oracle_usage', 'staking_adoption']
    },
    'DOT/USDT': {
        'reason': 'Parachain auctions, governance, treasury funding',
        'scorer': 'regulatory',
        'key_metrics': ['parachain_success', 'governance_participation', 'treasury_activity']
    },
}

# ==========================================
# Scoring Thresholds
# ==========================================

REGULATORY_SCORE_THRESHOLDS = {
    'STRONG_BUY': 85,   # 85-100: High confidence
    'BUY': 70,          # 70-84: Moderate confidence
    'WATCH': 50,        # 50-69: Monitor, don't trade
    'AVOID': 30,        # 30-49: Weak fundamentals
    'FREEZE': 0,        # 0-29: Red flags, stay away
}

# ==========================================
# Data Source Configuration
# ==========================================

DATA_SOURCES = {
    'github': {
        'enabled': True,
        'rate_limit': 60,  # requests per hour (unauthenticated)
        'cache_ttl': 3600,  # 1 hour cache
    },
    'etf_flows': {
        'enabled': True,
        'source': 'web_scraping',  # SoSo Value
        'cache_ttl': 3600,
    },
    'news': {
        'enabled': True,
        'source': 'cryptopanic_free',
        'cache_ttl': 1800,  # 30 minutes
    },
    'partnerships': {
        'enabled': True,
        'source': 'web_search',
        'cache_ttl': 86400,  # 24 hours
    },
}

# ==========================================
# Regulatory Scoring Weights
# ==========================================

REGULATORY_WEIGHTS = {
    'regulatory_progress': 40,      # /40 points
    'institutional_adoption': 30,   # /30 points
    'ecosystem_development': 20,    # /20 points
    'market_position': 10,          # /10 points
}

# Breakdown of Regulatory Progress (40 points)
REGULATORY_BREAKDOWN = {
    'legal_status': 15,       # SEC clarity, compliance, lawsuit resolution
    'etf_status': 15,         # ETF approvals, inflow trends
    'global_regulation': 10,  # Regulatory approval in major jurisdictions
}

# Breakdown of Institutional Adoption (30 points)
INSTITUTIONAL_BREAKDOWN = {
    'partnerships': 15,       # Major banks, payment processors
    'integration_progress': 10,  # Actual usage, deployed systems
    'corporate_holdings': 5,  # Companies holding on balance sheet
}

# Breakdown of Ecosystem Development (20 points)
ECOSYSTEM_BREAKDOWN = {
    'developer_activity': 10,  # GitHub commits, upgrades, dApps
    'network_growth': 10,      # Transaction volume, active addresses
}

# Breakdown of Market Position (10 points)
MARKET_BREAKDOWN = {
    'price_vs_ma200': 5,      # Distance from long-term average
    'relative_strength': 5,   # Performance vs BTC
}

# ==========================================
# Database Configuration
# ==========================================

INTELLIGENCE_DB_PATH = 'intelligence.db'  # Separate from trades_v3_paper.db

# Cache TTLs (seconds)
CACHE_TTLS = {
    'github_data': 3600,        # 1 hour
    'etf_flows': 3600,          # 1 hour
    'news_sentiment': 1800,     # 30 minutes
    'partnerships': 86400,      # 24 hours
    'price_data': 300,          # 5 minutes
}
