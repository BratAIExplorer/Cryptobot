"""
Centralized Exchange Adapter Configuration
Manages configuration for all exchange adapters with priority-based loading

Configuration Priority (highest to lowest):
1. Environment variables (MEXC_MAKER_FEE, etc.)
2. JSON config file (config/exchanges.json)
3. Defaults (defined in this module)
"""
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AdapterConfig:
    """
    Centralized configuration management for exchange adapters

    Features:
    - Default configurations for all exchanges
    - JSON file configuration support
    - Environment variable overrides
    - Validation and type checking
    """

    # Default configurations for all supported exchanges
    DEFAULTS = {
        'MEXC': {
            # Fees
            'maker_fee': 0.0000,  # 0.00% maker fee
            'taker_fee': 0.0005,  # 0.05% taker fee

            # Connection Management
            'idle_timeout_seconds': 300,  # 5 minutes
            'rate_limit': 100,  # Requests per second
            'connection_timeout_ms': 30000,  # 30 seconds

            # Reliability
            'heartbeat_interval': 60,  # 1 minute
            'max_retries': 3,
            'retry_delay_seconds': 2,

            # Health Monitoring
            'health_check_interval': 60,  # 1 minute
            'latency_warning_ms': 1000,  # 1 second
            'latency_critical_ms': 2000,  # 2 seconds

            # Trading
            'min_order_size_usdt': 10,  # Minimum order size
            'precision_price': 8,
            'precision_amount': 8
        },

        'BINANCE': {
            # Fees
            'maker_fee': 0.001,  # 0.1% maker fee
            'taker_fee': 0.001,  # 0.1% taker fee

            # Connection Management
            'idle_timeout_seconds': 300,
            'rate_limit': 50,  # More conservative for Binance
            'connection_timeout_ms': 30000,

            # Reliability
            'heartbeat_interval': 60,
            'max_retries': 3,
            'retry_delay_seconds': 2,

            # Health Monitoring
            'health_check_interval': 60,
            'latency_warning_ms': 1000,
            'latency_critical_ms': 2000,

            # Trading
            'min_order_size_usdt': 10,
            'precision_price': 8,
            'precision_amount': 8
        },

        'LUNO': {
            # Fees
            'maker_fee': 0.001,  # 0.1% maker fee (check Luno docs)
            'taker_fee': 0.001,  # 0.1% taker fee

            # Connection Management
            'idle_timeout_seconds': 300,
            'rate_limit': 60,
            'connection_timeout_ms': 30000,

            # Reliability
            'heartbeat_interval': 60,
            'max_retries': 3,
            'retry_delay_seconds': 2,

            # Health Monitoring
            'health_check_interval': 60,
            'latency_warning_ms': 1000,
            'latency_critical_ms': 2000,

            # Trading
            'min_order_size_usdt': 10,
            'precision_price': 8,
            'precision_amount': 8
        }
    }

    @staticmethod
    def get_config(exchange_name: str, mode: str = 'paper') -> Dict[str, Any]:
        """
        Get complete configuration for an exchange adapter

        Priority:
        1. Environment variables (highest)
        2. JSON config file
        3. Defaults (lowest)

        Args:
            exchange_name: Exchange name (MEXC, BINANCE, LUNO)
            mode: Trading mode (paper, live)

        Returns:
            Dictionary with complete configuration

        Example:
            >>> config = AdapterConfig.get_config('MEXC', 'paper')
            >>> print(config['maker_fee'])
            0.0
        """
        exchange_name = exchange_name.upper()

        # Validate exchange name
        if exchange_name not in AdapterConfig.DEFAULTS:
            available = list(AdapterConfig.DEFAULTS.keys())
            raise ValueError(
                f"Unsupported exchange: {exchange_name}. "
                f"Available: {', '.join(available)}"
            )

        # Start with defaults
        config = AdapterConfig.DEFAULTS[exchange_name].copy()
        logger.debug(f"[AdapterConfig] Loaded defaults for {exchange_name}")

        # Load from JSON if exists
        json_config = AdapterConfig._load_json_config()
        if exchange_name in json_config:
            config.update(json_config[exchange_name])
            logger.debug(f"[AdapterConfig] Applied JSON config for {exchange_name}")

        # Override with environment variables (highest priority)
        env_config = AdapterConfig._load_env_config(exchange_name)
        if env_config:
            config.update(env_config)
            logger.debug(f"[AdapterConfig] Applied env overrides for {exchange_name}")

        # Add credentials
        config['api_key'] = os.getenv(f'{exchange_name}_API_KEY')
        config['secret'] = os.getenv(f'{exchange_name}_SECRET_KEY')
        config['mode'] = mode
        config['exchange_name'] = exchange_name

        return config

    @staticmethod
    def _load_json_config() -> Dict:
        """
        Load configuration from config/exchanges.json

        Returns:
            Dictionary with exchange configurations or empty dict if not found
        """
        config_path = 'config/exchanges.json'

        if not os.path.exists(config_path):
            logger.debug(f"[AdapterConfig] JSON config not found: {config_path}")
            return {}

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"[AdapterConfig] Loaded JSON config from {config_path}")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"[AdapterConfig] Invalid JSON in {config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"[AdapterConfig] Failed to load {config_path}: {e}")
            return {}

    @staticmethod
    def _load_env_config(exchange_name: str) -> Dict:
        """
        Load configuration from environment variables

        Environment variable format: {EXCHANGE}_{PARAM_NAME}
        Example: MEXC_MAKER_FEE=0.0001

        Args:
            exchange_name: Exchange name (MEXC, BINANCE, LUNO)

        Returns:
            Dictionary with environment variable overrides
        """
        env_config = {}

        # Float parameters
        float_params = [
            'maker_fee', 'taker_fee'
        ]

        # Integer parameters
        int_params = [
            'idle_timeout_seconds', 'rate_limit', 'connection_timeout_ms',
            'heartbeat_interval', 'max_retries', 'retry_delay_seconds',
            'health_check_interval', 'latency_warning_ms', 'latency_critical_ms',
            'min_order_size_usdt', 'precision_price', 'precision_amount'
        ]

        # Check float parameters
        for param in float_params:
            env_var = f'{exchange_name}_{param.upper()}'
            value = os.getenv(env_var)
            if value is not None:
                try:
                    env_config[param] = float(value)
                    logger.debug(f"[AdapterConfig] Env override: {param}={value}")
                except ValueError:
                    logger.warning(f"[AdapterConfig] Invalid float for {env_var}: {value}")

        # Check integer parameters
        for param in int_params:
            env_var = f'{exchange_name}_{param.upper()}'
            value = os.getenv(env_var)
            if value is not None:
                try:
                    env_config[param] = int(value)
                    logger.debug(f"[AdapterConfig] Env override: {param}={value}")
                except ValueError:
                    logger.warning(f"[AdapterConfig] Invalid int for {env_var}: {value}")

        return env_config

    @staticmethod
    def create_template_config(output_path: str = 'config/exchanges.json'):
        """
        Create a template configuration file with all defaults

        Args:
            output_path: Path to save template (default: config/exchanges.json)

        Example:
            >>> AdapterConfig.create_template_config()
            ✅ Template created at config/exchanges.json
        """
        # Create config directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Create template with comments
        template = {
            "_comment": "Exchange adapter configuration - Override defaults here",
            "_priority": "This file overrides defaults, env vars override this file",
            "MEXC": AdapterConfig.DEFAULTS['MEXC'].copy(),
            "BINANCE": AdapterConfig.DEFAULTS['BINANCE'].copy(),
            "LUNO": AdapterConfig.DEFAULTS['LUNO'].copy()
        }

        # Save to file
        try:
            with open(output_path, 'w') as f:
                json.dump(template, f, indent=2)
            logger.info(f"✅ Configuration template created: {output_path}")
            print(f"✅ Configuration template created: {output_path}")
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            print(f"❌ Failed to create template: {e}")

    @staticmethod
    def validate_config(config: Dict) -> bool:
        """
        Validate configuration dictionary

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_keys = [
            'maker_fee', 'taker_fee', 'rate_limit',
            'connection_timeout_ms', 'heartbeat_interval'
        ]

        for key in required_keys:
            if key not in config:
                logger.error(f"[AdapterConfig] Missing required key: {key}")
                return False

        # Validate fee ranges
        if not (0 <= config['maker_fee'] <= 0.01):
            logger.warning(f"[AdapterConfig] Unusual maker_fee: {config['maker_fee']}")

        if not (0 <= config['taker_fee'] <= 0.01):
            logger.warning(f"[AdapterConfig] Unusual taker_fee: {config['taker_fee']}")

        return True

    @staticmethod
    def get_all_supported_exchanges() -> list:
        """
        Get list of all supported exchanges

        Returns:
            List of exchange names
        """
        return list(AdapterConfig.DEFAULTS.keys())

    @staticmethod
    def get_exchange_info(exchange_name: str) -> Dict:
        """
        Get human-readable info about an exchange

        Args:
            exchange_name: Exchange name

        Returns:
            Dictionary with exchange information
        """
        exchange_name = exchange_name.upper()

        if exchange_name not in AdapterConfig.DEFAULTS:
            return {'error': 'Exchange not supported'}

        config = AdapterConfig.DEFAULTS[exchange_name]

        return {
            'name': exchange_name,
            'maker_fee': f"{config['maker_fee']*100:.2f}%",
            'taker_fee': f"{config['taker_fee']*100:.2f}%",
            'rate_limit': f"{config['rate_limit']} req/s",
            'min_order': f"${config['min_order_size_usdt']}",
            'heartbeat': f"{config['heartbeat_interval']}s"
        }


# CLI tool for configuration management
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Exchange Adapter Configuration Manager")
    print("=" * 60)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'template':
            # Create template
            AdapterConfig.create_template_config()

        elif command == 'info':
            # Show exchange info
            if len(sys.argv) > 2:
                exchange = sys.argv[2]
                info = AdapterConfig.get_exchange_info(exchange)
                print(f"\n{exchange.upper()} Configuration:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print("\nSupported Exchanges:")
                for exchange in AdapterConfig.get_all_supported_exchanges():
                    print(f"  - {exchange}")

        elif command == 'test':
            # Test configuration loading
            exchange = sys.argv[2] if len(sys.argv) > 2 else 'MEXC'
            print(f"\nTesting configuration for {exchange}...")
            config = AdapterConfig.get_config(exchange, 'paper')
            print(f"Maker Fee: {config['maker_fee']*100:.3f}%")
            print(f"Taker Fee: {config['taker_fee']*100:.3f}%")
            print(f"Heartbeat: {config['heartbeat_interval']}s")
            print(f"API Key Set: {'Yes' if config['api_key'] else 'No'}")

        else:
            print(f"Unknown command: {command}")

    else:
        print("\nUsage:")
        print("  python adapter_config.py template  - Create config template")
        print("  python adapter_config.py info [EXCHANGE] - Show exchange info")
        print("  python adapter_config.py test [EXCHANGE] - Test configuration")
