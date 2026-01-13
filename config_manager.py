"""
CryptoBots V3 - Configuration Manager
Handles saving/loading bot configurations with encryption for sensitive data.
"""

import json
import os
from typing import Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
import base64


class ConfigManager:
    """
    Manages bot configuration with encryption for sensitive data.
    Stores configs in JSON format with API keys encrypted.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "bot_config.json"
        self.key_file = self.config_dir / ".encryption_key"
        
        self._init_encryption()
        self.config = self._load_config()
    
    def _init_encryption(self):
        """Initialize or load encryption key."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Hide the key file on Windows
            if os.name == 'nt':
                os.system(f'attrib +h "{self.key_file}"')
        
        self.cipher = Fernet(key)
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not data:
            return ""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not encrypted_data:
            return ""
        try:
            decoded = base64.b64decode(encrypted_data.encode())
            return self.cipher.decrypt(decoded).decode()
        except Exception:
            return ""
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Decrypt sensitive fields
            if 'exchange' in config and 'api_key' in config['exchange']:
                config['exchange']['api_key'] = self._decrypt(config['exchange']['api_key'])
                config['exchange']['api_secret'] = self._decrypt(config['exchange']['api_secret'])
            
            return config
        except Exception as e:
            print(f"⚠️ Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'exchange': {
                'name': 'binance',
                'api_key': '',
                'api_secret': '',
                'testnet': True
            },
            'trading': {
                'symbols': ['BTC/USDT'],
                'max_concurrent_positions': 3,
                'total_balance_allocation_percent': 30.0
            },
            'strategies': {
                'buy_dip': {
                    'enabled': True,
                    'dip_percentage': 5.0,
                    'cooldown_hours': 4,
                    'position_size_percent': 10.0,
                    'stop_loss_percent': 2.0
                },
                'take_profit': {
                    'enabled': True,
                    'profit_target_percent': 3.0,
                    'trailing_stop_percent': 1.0,
                    'stop_loss_percent': 2.0,
                    'position_size_percent': 10.0
                },
                'trend_following': {
                    'enabled': False,
                    'fast_ma_period': 50,
                    'slow_ma_period': 200,
                    'max_drawdown_percent': 5.0,
                    'position_size_percent': 15.0
                }
            },
            'risk_management': {
                'max_daily_loss_percent': 5.0,
                'max_position_loss_percent': 2.0,
                'emergency_stop_enabled': True
            },
            'notifications': {
                'email_enabled': False,
                'email_address': '',
                'send_on_trade': True,
                'send_on_error': True
            }
        }
    
    def save_config(self, config: Dict[str, Any] = None):
        """
        Save configuration to file.
        
        Args:
            config: Configuration dict to save (uses current if None)
        """
        if config:
            self.config = config
        
        # Create copy for encryption
        save_config = self.config.copy()
        
        # Encrypt sensitive fields
        if 'exchange' in save_config:
            exchange = save_config['exchange'].copy()
            if 'api_key' in exchange:
                exchange['api_key'] = self._encrypt(exchange['api_key'])
            if 'api_secret' in exchange:
                exchange['api_secret'] = self._encrypt(exchange['api_secret'])
            save_config['exchange'] = exchange
        
        # Save to file
        with open(self.config_file, 'w') as f:
            json.dump(save_config, f, indent=2)
        
        print(f"✅ Configuration saved to {self.config_file}")
    
    def get(self, key_path: str, default=None) -> Any:
        """
        Get configuration value by dot-notation path.
        
        Args:
            key_path: Dot-separated path (e.g., 'strategies.buy_dip.enabled')
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value by dot-notation path.
        
        Args:
            key_path: Dot-separated path (e.g., 'strategies.buy_dip.enabled')
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_strategy_config(self, strategy_name: str) -> Dict:
        """
        Get configuration for a specific strategy.
        
        Args:
            strategy_name: Name of strategy (buy_dip, take_profit, etc.)
            
        Returns:
            Strategy configuration dict
        """
        return self.get(f'strategies.{strategy_name}', {})
    
    def update_strategy_config(self, strategy_name: str, config: Dict):
        """
        Update configuration for a specific strategy.
        
        Args:
            strategy_name: Name of strategy
            config: New configuration dict
        """
        if 'strategies' not in self.config:
            self.config['strategies'] = {}
        
        self.config['strategies'][strategy_name] = config
        self.save_config()
    
    def export_config(self, filepath: str):
        """Export configuration to a file (without sensitive data)."""
        export_config = self.config.copy()
        
        # Remove sensitive data
        if 'exchange' in export_config:
            export_config['exchange']['api_key'] = '***'
            export_config['exchange']['api_secret'] = '***'
        
        with open(filepath, 'w') as f:
            json.dump(export_config, f, indent=2)
        
        print(f"✅ Configuration exported to {filepath}")
    
    def import_config(self, filepath: str):
        """Import configuration from a file."""
        with open(filepath, 'r') as f:
            imported = json.load(f)
        
        # Don't overwrite API keys if they're masked
        if 'exchange' in imported:
            if imported['exchange'].get('api_key') == '***':
                imported['exchange']['api_key'] = self.config['exchange'].get('api_key', '')
            if imported['exchange'].get('api_secret') == '***':
                imported['exchange']['api_secret'] = self.config['exchange'].get('api_secret', '')
        
        self.config = imported
        self.save_config()
        
        print(f"✅ Configuration imported from {filepath}")
