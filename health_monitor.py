"""
CryptoBots V3 - Health Monitor
Constantly monitors bot health to prevent disasters and ensure safe operation.
"""

import ccxt
import psutil
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


class HealthMonitor:
    """
    Monitors trading bot health across multiple dimensions:
    - API connectivity and rate limits
    - Data freshness and latency
    - System resources (CPU, RAM, Disk)
    - Balance changes and emergency conditions
    """
    
    def __init__(self, exchange_id: str = 'binance', api_key: str = None, api_secret: str = None):
        """
        Initialize the health monitor.
        
        Args:
            exchange_id: Exchange to monitor (default: binance)
            api_key: Exchange API key (optional for public data)
            api_secret: Exchange API secret (optional for public data)
        """
        self.exchange_id = exchange_id
        self.exchange = None
        self.last_heartbeat = None
        self.last_price_update = None
        self.initial_balance = None
        self.health_status = {
            'heartbeat': 'UNKNOWN',
            'api_connection': 'UNKNOWN',
            'data_freshness': 'UNKNOWN',
            'system_vitals': 'UNKNOWN',
            'balance_check': 'UNKNOWN',
            'emergency_stop': False
        }
        
        # Initialize exchange connection
        self._init_exchange(api_key, api_secret)
        
    def _init_exchange(self, api_key: Optional[str], api_secret: Optional[str]):
        """Initialize exchange connection."""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            
            config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
            
            if api_key and api_secret:
                config['apiKey'] = api_key
                config['secret'] = api_secret
                
            self.exchange = exchange_class(config)
            print(f"✅ Initialized {self.exchange_id} connection")
            
        except Exception as e:
            print(f"❌ Failed to initialize exchange: {e}")
            self.health_status['api_connection'] = 'CRITICAL'
    
    def check_heartbeat(self) -> Tuple[str, str]:
        """
        Check if the monitor itself is alive.
        
        Returns:
            Tuple of (status, message)
        """
        current_time = datetime.now()
        
        if self.last_heartbeat:
            time_since_last = (current_time - self.last_heartbeat).total_seconds()
            if time_since_last > 120:  # 2 minutes without heartbeat
                return 'WARNING', f'No heartbeat for {time_since_last:.0f}s'
        
        self.last_heartbeat = current_time
        return 'OK', 'Heartbeat active'
    
    def check_api_connection(self, test_symbol: str = 'BTC/USDT') -> Tuple[str, str]:
        """
        Test API connectivity and detect common issues.
        
        Args:
            test_symbol: Symbol to test price fetching
            
        Returns:
            Tuple of (status, message)
        """
        if not self.exchange:
            return 'CRITICAL', 'Exchange not initialized'
        
        try:
            # Test public API endpoint
            ticker = self.exchange.fetch_ticker(test_symbol)
            
            if ticker and 'last' in ticker:
                self.last_price_update = datetime.now()
                return 'OK', f'{self.exchange_id} API responding (${ticker["last"]:,.2f})'
            else:
                return 'WARNING', 'API responded but data incomplete'
                
        except ccxt.AuthenticationError as e:
            return 'WARNING', f'Auth issue (using public data only): {str(e)[:50]}'
        except ccxt.RateLimitExceeded:
            return 'WARNING', 'Rate limit exceeded - throttling'
        except ccxt.NetworkError as e:
            return 'CRITICAL', f'Network error: {str(e)[:50]}'
        except Exception as e:
            return 'CRITICAL', f'API error: {str(e)[:50]}'
    
    def check_data_freshness(self, max_age_seconds: int = 10) -> Tuple[str, str]:
        """
        Check if price data is fresh enough for trading.
        
        Args:
            max_age_seconds: Maximum acceptable data age
            
        Returns:
            Tuple of (status, message)
        """
        if not self.last_price_update:
            return 'WARNING', 'No price data yet'
        
        age = (datetime.now() - self.last_price_update).total_seconds()
        
        if age > max_age_seconds * 2:
            return 'CRITICAL', f'Stale data ({age:.1f}s old)'
        elif age > max_age_seconds:
            return 'WARNING', f'Data aging ({age:.1f}s old)'
        else:
            return 'OK', f'Data fresh ({age:.1f}s)'
    
    def check_system_vitals(self) -> Tuple[str, Dict[str, float]]:
        """
        Check system resource usage.
        
        Returns:
            Tuple of (status, vitals_dict)
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            vitals = {
                'cpu_percent': cpu_percent,
                'ram_percent': memory.percent,
                'disk_percent': disk.percent
            }
            
            # Determine overall status
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
                status = 'CRITICAL'
            elif cpu_percent > 70 or memory.percent > 80 or disk.percent > 90:
                status = 'WARNING'
            else:
                status = 'OK'
            
            return status, vitals
            
        except Exception as e:
            return 'WARNING', {'error': str(e)}
    
    def check_balance(self, symbol: str = 'USDT', max_drop_percent: float = 10.0) -> Tuple[str, str]:
        """
        Check account balance for rapid drops (possible bug/hack).
        
        Args:
            symbol: Balance symbol to check
            max_drop_percent: Max acceptable drop percentage
            
        Returns:
            Tuple of (status, message)
        """
        if not self.exchange:
            return 'UNKNOWN', 'Exchange not initialized'
        
        try:
            # Fetch balance (requires API keys)
            balance = self.exchange.fetch_balance()
            
            if symbol not in balance['total']:
                return 'WARNING', f'{symbol} balance not found'
            
            current_balance = balance['total'][symbol]
            
            # Initialize baseline
            if self.initial_balance is None:
                self.initial_balance = current_balance
                return 'OK', f'Baseline set: ${current_balance:,.2f}'
            
            # Calculate drop percentage
            drop_percent = ((self.initial_balance - current_balance) / self.initial_balance) * 100
            
            if drop_percent > max_drop_percent:
                self.health_status['emergency_stop'] = True
                return 'CRITICAL', f'⚠️ EMERGENCY: {drop_percent:.1f}% drop detected!'
            elif drop_percent > max_drop_percent / 2:
                return 'WARNING', f'Balance dropped {drop_percent:.1f}%'
            else:
                return 'OK', f'Balance: ${current_balance:,.2f} ({drop_percent:+.2f}%)'
                
        except ccxt.AuthenticationError:
            return 'UNKNOWN', 'API keys required for balance check'
        except Exception as e:
            return 'WARNING', f'Balance check failed: {str(e)[:50]}'
    
    def run_full_check(self, debug: bool = False) -> Dict[str, any]:
        """
        Run all health checks and return comprehensive status.
        
        Args:
            debug: Print detailed output
            
        Returns:
            Dictionary with all health metrics
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Run all checks
        heartbeat_status, heartbeat_msg = self.check_heartbeat()
        api_status, api_msg = self.check_api_connection()
        data_status, data_msg = self.check_data_freshness()
        system_status, system_vitals = self.check_system_vitals()
        balance_status, balance_msg = self.check_balance()
        
        # Update health status
        self.health_status.update({
            'timestamp': timestamp,
            'heartbeat': {'status': heartbeat_status, 'message': heartbeat_msg},
            'api_connection': {'status': api_status, 'message': api_msg},
            'data_freshness': {'status': data_status, 'message': data_msg},
            'system_vitals': {'status': system_status, 'vitals': system_vitals},
            'balance_check': {'status': balance_status, 'message': balance_msg}
        })
        
        # Print if debug mode
        if debug:
            self._print_status()
        
        # Save to file
        self._save_status()
        
        return self.health_status
    
    def _print_status(self):
        """Print formatted health status to console."""
        print(f"\n{'='*60}")
        print(f"🏥 Health Monitor Report - {self.health_status['timestamp']}")
        print(f"{'='*60}")
        
        for check_name in ['heartbeat', 'api_connection', 'data_freshness', 'system_vitals', 'balance_check']:
            check_data = self.health_status[check_name]
            
            if isinstance(check_data, dict) and 'status' in check_data:
                status = check_data['status']
                emoji = {'OK': '🟢', 'WARNING': '🟡', 'CRITICAL': '🔴', 'UNKNOWN': '⚪'}.get(status, '⚪')
                
                print(f"{emoji} {check_name.replace('_', ' ').title()}: {status}")
                
                if check_name == 'system_vitals' and 'vitals' in check_data:
                    vitals = check_data['vitals']
                    print(f"   └─ CPU: {vitals.get('cpu_percent', 0):.1f}% | "
                          f"RAM: {vitals.get('ram_percent', 0):.1f}% | "
                          f"Disk: {vitals.get('disk_percent', 0):.1f}%")
                elif 'message' in check_data:
                    print(f"   └─ {check_data['message']}")
        
        if self.health_status['emergency_stop']:
            print(f"\n🚨 EMERGENCY STOP ACTIVATED 🚨")
        
        print(f"{'='*60}\n")
    
    def _save_status(self, filename: str = 'health_status.json'):
        """Save health status to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.health_status, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save health status: {e}")
    
    def should_stop_trading(self) -> bool:
        """
        Determine if trading should be stopped based on health checks.
        
        Returns:
            True if trading should stop
        """
        # Emergency stop triggered
        if self.health_status['emergency_stop']:
            return True
        
        # Critical API issues
        if isinstance(self.health_status['api_connection'], dict):
            if self.health_status['api_connection'].get('status') == 'CRITICAL':
                return True
        
        # Stale data
        if isinstance(self.health_status['data_freshness'], dict):
            if self.health_status['data_freshness'].get('status') == 'CRITICAL':
                return True
        
        return False


def main():
    """Main entry point for standalone health monitor."""
    parser = argparse.ArgumentParser(description='CryptoBots V3 Health Monitor')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--exchange', type=str, default='binance', help='Exchange to monitor')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Health Monitor for {args.exchange}")
    print(f"⏱️ Check interval: {args.interval}s")
    
    monitor = HealthMonitor(exchange_id=args.exchange)
    
    try:
        while True:
            monitor.run_full_check(debug=args.debug)
            
            if monitor.should_stop_trading():
                print("🛑 CRITICAL ISSUES DETECTED - TRADING SHOULD BE STOPPED")
            
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n👋 Health Monitor stopped by user")


if __name__ == '__main__':
    main()
