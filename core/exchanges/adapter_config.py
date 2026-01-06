import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AdapterConfig:
    """
    Centralized Configuration for Exchange Adapters.
    Priority:
    1. Environment Variables (e.g., MEXC_API_KEY)
    2. JSON Config File (config/exchanges.json)
    3. Hardcoded Defaults
    """
    
    DEFAULT_CONFIG = {
        'MEXC': {
            'timeout': 30000,
            'rate_limit': 100,
            'maker_fee': 0.000,
            'taker_fee': 0.001
        },
        'BINANCE': {
            'timeout': 30000,
            'rate_limit': 50,
            'maker_fee': 0.001,
            'taker_fee': 0.001
        },
        'LUNO': {
            'timeout': 30000,
            'rate_limit': 1000,
            'maker_fee': 0.004,
            'taker_fee': 0.006
        }
    }

    def __init__(self, config_path: str = 'config/exchanges.json'):
        self.config_path = config_path
        self.file_config = self._load_file_config()

    def _load_file_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ Failed to load config file {self.config_path}: {e}")
        return {}

    def get_config(self, exchange_name: str) -> Dict[str, Any]:
        """
        Get merged configuration for an exchange.
        """
        exchange_name = exchange_name.upper()
        
        # 1. Defaults
        config = self.DEFAULT_CONFIG.get(exchange_name, {}).copy()
        
        # 2. File Overrides
        file_conf = self.file_config.get(exchange_name, {})
        config.update(file_conf)
        
        # 3. Env Var Overrides (Specific keys)
        # API Keys are ALWAYS Env Vars for security
        if exchange_name == 'MEXC':
            config['apiKey'] = os.environ.get('MEXC_API_KEY')
            config['secret'] = os.environ.get('MEXC_SECRET_KEY')
        elif exchange_name == 'BINANCE':
            config['apiKey'] = os.environ.get('BINANCE_API_KEY')
            config['secret'] = os.environ.get('BINANCE_SECRET_KEY')
        elif exchange_name == 'LUNO':
            config['apiKey'] = os.environ.get('LUNO_API_KEY')
            config['secret'] = os.environ.get('LUNO_SECRET')
            
        return config

    def validate_keys(self, exchange_name: str) -> bool:
        """Check if API keys are present."""
        config = self.get_config(exchange_name)
        return bool(config.get('apiKey') and config.get('secret'))
