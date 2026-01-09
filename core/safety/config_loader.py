"""
Safety Configuration Loader - 100% Customizable

Loads safety limits from YAML configuration files.
Supports:
- Exchange-specific configs
- Mode-specific configs (paper/live/monitor)
- Strategy-specific overrides
- Scaling presets
- Emergency overrides

Design: Hierarchical override system (most specific wins)
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SafetyConfigLoader:
    """
    Load and manage safety configuration with hierarchical overrides

    Priority (highest to lowest):
    1. Emergency overrides
    2. Strategy-specific
    3. Exchange + Mode specific
    4. Exchange default
    5. Global defaults
    """

    def __init__(self, config_file: str = 'config/safety_limits.yaml'):
        """
        Initialize config loader

        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()

        logger.info(f"Safety config loaded from: {config_file}")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            config_path = Path(self.config_file)

            if not config_path.exists():
                logger.warning(f"Config file not found: {self.config_file}, using defaults")
                return self._get_hardcoded_defaults()

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"✅ Configuration loaded successfully")
                return config

        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return self._get_hardcoded_defaults()

    def _get_hardcoded_defaults(self) -> Dict:
        """Fallback defaults if YAML not found (robustness)"""
        return {
            'defaults': {
                'kill_switch': {
                    'max_daily_loss_usd': 50.0,
                    'max_weekly_loss_usd': 150.0,
                },
                'capital_limits': {
                    'max_position_size_usd': 250.0,
                    'max_open_positions': 4,
                    'max_total_exposure_usd': 1000.0,
                    'max_daily_trades': 20,
                    'min_account_balance_usd': 100.0,
                },
                'reconciliation': {
                    'tolerance_usd': 1.0,
                    'check_interval_seconds': 300,
                },
                'slippage_protection': {
                    'max_slippage_percent': 0.2,
                    'order_timeout_seconds': 30,
                    'enable_protection': True,
                },
            }
        }

    def get_kill_switch_config(
        self,
        exchange: str,
        mode: str,
        strategy: Optional[str] = None,
        scaling_preset: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get kill switch configuration with all overrides applied

        Args:
            exchange: Exchange name (BINANCE, LUNO, MEXC)
            mode: Trading mode (paper, live, monitor)
            strategy: Optional strategy name for overrides
            scaling_preset: Optional preset (micro, small, medium, large)

        Returns:
            Dict with kill switch parameters
        """
        config = self._get_merged_config('kill_switch', exchange, mode, strategy, scaling_preset)

        logger.info(f"Kill switch config for {exchange}/{mode}: {config}")
        return config

    def get_capital_limits_config(
        self,
        exchange: str,
        mode: str,
        strategy: Optional[str] = None,
        scaling_preset: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get capital limits configuration"""
        config = self._get_merged_config('capital_limits', exchange, mode, strategy, scaling_preset)

        logger.info(f"Capital limits config for {exchange}/{mode}: {config}")
        return config

    def get_reconciliation_config(
        self,
        exchange: str,
        mode: str,
        strategy: Optional[str] = None,
        scaling_preset: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get reconciliation configuration"""
        config = self._get_merged_config('reconciliation', exchange, mode, strategy, scaling_preset)

        logger.info(f"Reconciliation config for {exchange}/{mode}: {config}")
        return config

    def get_slippage_protection_config(
        self,
        exchange: str,
        mode: str,
        strategy: Optional[str] = None,
        scaling_preset: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get slippage protection configuration"""
        config = self._get_merged_config('slippage_protection', exchange, mode, strategy, scaling_preset)

        logger.info(f"Slippage protection config for {exchange}/{mode}: {config}")
        return config

    def _get_merged_config(
        self,
        component: str,
        exchange: str,
        mode: str,
        strategy: Optional[str] = None,
        scaling_preset: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Merge configuration with hierarchical overrides

        Priority (highest to lowest):
        1. Emergency overrides
        2. Scaling preset
        3. Strategy-specific
        4. Exchange + Mode specific
        5. Global defaults
        """
        # Start with global defaults
        config = self.config.get('defaults', {}).get(component, {}).copy()

        # Apply exchange-specific defaults
        exchange_config = self.config.get('exchanges', {}).get(exchange.upper(), {})
        if component in exchange_config:
            config.update(exchange_config[component])

        # Apply mode-specific overrides
        mode_config = exchange_config.get(mode.lower(), {})
        if component in mode_config:
            config.update(mode_config[component])

        # Apply strategy-specific overrides
        if strategy:
            strategy_config = self.config.get('strategies', {}).get(strategy, {})
            if component in strategy_config:
                config.update(strategy_config[component])
                logger.info(f"Applied strategy override: {strategy}")

        # Apply scaling preset
        if scaling_preset:
            preset_config = self.config.get('scaling_presets', {}).get(scaling_preset, {})
            if component in preset_config:
                config.update(preset_config[component])
                logger.info(f"Applied scaling preset: {scaling_preset}")

        # Apply emergency overrides (highest priority)
        emergency = self.config.get('emergency', {})
        if emergency.get('global_halt', False):
            logger.critical("🚨 GLOBAL HALT ENABLED IN CONFIG")
            # This will be handled by caller

        temp_limits = emergency.get('temporary_limits', {})
        if temp_limits.get('enabled', False):
            # Apply temporary overrides
            if component == 'kill_switch' and temp_limits.get('max_daily_loss_override'):
                config['max_daily_loss_usd'] = temp_limits['max_daily_loss_override']
                logger.warning(f"Applied temporary daily loss override: {temp_limits['max_daily_loss_override']}")

            if component == 'capital_limits' and temp_limits.get('max_position_size_override'):
                config['max_position_size_usd'] = temp_limits['max_position_size_override']
                logger.warning(f"Applied temporary position size override: {temp_limits['max_position_size_override']}")

        return config

    def is_global_halt_enabled(self) -> bool:
        """Check if global halt is enabled in config"""
        return self.config.get('emergency', {}).get('global_halt', False)

    def get_authorization_code(self, code_type: str = 'kill_switch') -> str:
        """Get authorization code from config"""
        auth = self.config.get('authorization', {})

        if code_type == 'kill_switch':
            return auth.get('kill_switch_resume_code', 'RESUME_TRADING_2026')
        elif code_type == 'emergency':
            return auth.get('emergency_override_code', 'EMERGENCY_OVERRIDE_2026')
        else:
            return os.getenv('KILL_SWITCH_AUTH_CODE', 'RESUME_TRADING_2026')

    def get_state_file_path(self, exchange: str, mode: str, component: str) -> str:
        """
        Generate state file path for safety component

        Args:
            exchange: Exchange name
            mode: Trading mode
            component: Component name (kill_switch, etc)

        Returns:
            Full path to state file
        """
        base_dir = f'data/{exchange.lower()}/{mode.lower()}'
        os.makedirs(base_dir, exist_ok=True)

        return f'{base_dir}/{component}_state.json'

    def reload_config(self):
        """Reload configuration from file (for runtime updates)"""
        logger.info("Reloading safety configuration...")
        self.config = self._load_config()
        logger.info("✅ Configuration reloaded")

    def validate_config(self) -> bool:
        """
        Validate configuration for correctness

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required sections exist
            required_sections = ['defaults']
            for section in required_sections:
                if section not in self.config:
                    logger.error(f"Missing required section: {section}")
                    return False

            # Validate numeric values
            defaults = self.config.get('defaults', {})

            kill_switch = defaults.get('kill_switch', {})
            if kill_switch.get('max_daily_loss_usd', 0) <= 0:
                logger.error("max_daily_loss_usd must be > 0")
                return False

            capital = defaults.get('capital_limits', {})
            if capital.get('max_position_size_usd', 0) <= 0:
                logger.error("max_position_size_usd must be > 0")
                return False

            logger.info("✅ Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def get_all_configs(
        self,
        exchange: str,
        mode: str,
        strategy: Optional[str] = None,
        scaling_preset: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        Get all safety configurations at once

        Returns:
            Dict with all component configs
        """
        return {
            'kill_switch': self.get_kill_switch_config(exchange, mode, strategy, scaling_preset),
            'capital_limits': self.get_capital_limits_config(exchange, mode, strategy, scaling_preset),
            'reconciliation': self.get_reconciliation_config(exchange, mode, strategy, scaling_preset),
            'slippage_protection': self.get_slippage_protection_config(exchange, mode, strategy, scaling_preset),
            'state_files': {
                'kill_switch': self.get_state_file_path(exchange, mode, 'kill_switch'),
                'reconciliation': self.get_state_file_path(exchange, mode, 'reconciliation'),
            },
            'authorization': {
                'kill_switch_code': self.get_authorization_code('kill_switch'),
                'emergency_code': self.get_authorization_code('emergency'),
            },
            'global_halt': self.is_global_halt_enabled(),
        }


# Singleton instance for global access
_config_loader = None

def get_safety_config(config_file: str = 'config/safety_limits.yaml') -> SafetyConfigLoader:
    """
    Get singleton config loader instance

    Args:
        config_file: Path to config file

    Returns:
        SafetyConfigLoader instance
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = SafetyConfigLoader(config_file)

    return _config_loader


# Example usage
if __name__ == "__main__":
    print("Safety Configuration Loader Test")
    print("=" * 60)

    # Initialize loader
    loader = SafetyConfigLoader('config/safety_limits.yaml')

    # Validate config
    is_valid = loader.validate_config()
    print(f"\nConfiguration valid: {is_valid}")

    # Test 1: Binance live config
    print("\n" + "=" * 60)
    print("Test 1: Binance LIVE configuration")
    print("=" * 60)

    binance_live = loader.get_all_configs(
        exchange='BINANCE',
        mode='live'
    )

    print("\nKill Switch:")
    for key, value in binance_live['kill_switch'].items():
        print(f"  {key}: {value}")

    print("\nCapital Limits:")
    for key, value in binance_live['capital_limits'].items():
        print(f"  {key}: {value}")

    # Test 2: Binance paper config
    print("\n" + "=" * 60)
    print("Test 2: Binance PAPER configuration")
    print("=" * 60)

    binance_paper = loader.get_all_configs(
        exchange='BINANCE',
        mode='paper'
    )

    print("\nKill Switch (should be more tolerant):")
    for key, value in binance_paper['kill_switch'].items():
        print(f"  {key}: {value}")

    # Test 3: Scaling preset
    print("\n" + "=" * 60)
    print("Test 3: Binance LIVE with MICRO preset ($100 capital)")
    print("=" * 60)

    binance_micro = loader.get_all_configs(
        exchange='BINANCE',
        mode='live',
        scaling_preset='micro'
    )

    print("\nKill Switch (micro limits):")
    for key, value in binance_micro['kill_switch'].items():
        print(f"  {key}: {value}")

    print("\nCapital Limits (micro limits):")
    for key, value in binance_micro['capital_limits'].items():
        print(f"  {key}: {value}")

    # Test 4: Strategy override
    print("\n" + "=" * 60)
    print("Test 4: Binance LIVE with GridBot strategy")
    print("=" * 60)

    binance_grid = loader.get_all_configs(
        exchange='BINANCE',
        mode='live',
        strategy='GridBot'
    )

    print("\nCapital Limits (GridBot specific):")
    for key, value in binance_grid['capital_limits'].items():
        print(f"  {key}: {value}")

    # Test 5: LUNO monitor mode
    print("\n" + "=" * 60)
    print("Test 5: LUNO MONITOR mode (no trading)")
    print("=" * 60)

    luno_monitor = loader.get_all_configs(
        exchange='LUNO',
        mode='monitor'
    )

    print("\nCapital Limits (should all be 0):")
    for key, value in luno_monitor['capital_limits'].items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("✅ All tests complete - Configuration system ready!")
    print("=" * 60)
    print("\nKey Features:")
    print("  ✓ 100% customizable via YAML")
    print("  ✓ Exchange-specific configs")
    print("  ✓ Mode-specific configs (paper/live/monitor)")
    print("  ✓ Strategy-specific overrides")
    print("  ✓ Scaling presets (micro/small/medium/large)")
    print("  ✓ Emergency overrides")
    print("  ✓ Hierarchical priority system")
    print("  ✓ Robust fallbacks if config missing")
    print("  ✓ Runtime reload capability")
    print("  ✓ Configuration validation")
