"""
Main Application Entry Point
Luno Portfolio Monitor
"""
import time
import schedule
from datetime import datetime
from colorama import init, Fore, Style
import config
from src.luno_client import LunoClient
from src.price_monitor import PriceMonitor
from src.alert_manager import AlertManager
from src.portfolio_analyzer import PortfolioAnalyzer

# Initialize colorama for colored console output
init()

class LunoPortfolioMonitor:
    """Main application class for portfolio monitoring"""
    
    def __init__(self):
        """Initialize all components"""
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}LUNO PORTFOLIO MONITOR{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        # Validate configuration
        try:
            config.validate_config()
            print(f"{Fore.GREEN}✓ Configuration validated{Style.RESET_ALL}")
        except ValueError as e:
            print(f"{Fore.RED}✗ Configuration error: {e}{Style.RESET_ALL}")
            raise
        
        # Initialize components
        print(f"\n{Fore.YELLOW}Initializing components...{Style.RESET_ALL}")
        
        self.luno_client = LunoClient()
        print(f"{Fore.GREEN}✓ Luno API client initialized{Style.RESET_ALL}")
        
        self.price_monitor = PriceMonitor()
        print(f"{Fore.GREEN}✓ Price monitor initialized{Style.RESET_ALL}")
        
        self.alert_manager = AlertManager()
        print(f"{Fore.GREEN}✓ Alert manager initialized{Style.RESET_ALL}")
        
        self.portfolio_analyzer = PortfolioAnalyzer()
        print(f"{Fore.GREEN}✓ Portfolio analyzer initialized{Style.RESET_ALL}")
        
        # Test Luno connection
        print(f"\n{Fore.YELLOW}Testing Luno API connection...{Style.RESET_ALL}")
        if self.luno_client.test_connection():
            print(f"{Fore.GREEN}✓ Successfully connected to Luno API{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Failed to connect to Luno API{Style.RESET_ALL}")
            raise ConnectionError("Could not connect to Luno API")
        
        # Track alerted targets to avoid duplicate alerts
        self.alerted_targets = {}
    
    def monitor_prices(self):
        """Main monitoring loop - check prices and send alerts"""
        try:
            print(f"\n{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] Checking prices...{Style.RESET_ALL}")
            
            # Get portfolio snapshot
            snapshot = self.portfolio_analyzer.get_portfolio_snapshot()
            
            # Check each holding for alerts
            for holding in snapshot['holdings']:
                coin = holding['coin']
                current_price = holding['current_price']
                target_prices = holding['target_prices']
                
                # Detect alerts
                alerts = self.price_monitor.detect_price_alerts(coin, current_price, target_prices)
                
                # Send alerts
                for alert in alerts:
                    alert_key = f"{coin}_{alert['type']}_{alert.get('profit_pct', alert.get('drop_pct'))}"
                    
                    # Avoid duplicate alerts (only alert once per target)
                    if alert_key not in self.alerted_targets:
                        if alert['type'] == 'target_reached':
                            self.alert_manager.send_profit_target_alert(alert)
                            self.alerted_targets[alert_key] = datetime.now()
                            print(f"{Fore.GREEN}🎯 {alert['message']}{Style.RESET_ALL}")
                        
                        elif alert['type'] == 'price_drop':
                            self.alert_manager.send_price_drop_alert(alert)
                            print(f"{Fore.RED}⚠️ {alert['message']}{Style.RESET_ALL}")
            
            # Display summary in MYR
            print(f"{Fore.CYAN}Portfolio Value: {self.portfolio_analyzer.currency.format_myr_primary(snapshot['total_value'])} ({snapshot['total_profit_pct']:+.2f}%){Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error during monitoring: {e}{Style.RESET_ALL}")
    
    def daily_summary(self):
        """Send daily portfolio summary"""
        try:
            print(f"\n{Fore.YELLOW}Generating daily summary...{Style.RESET_ALL}")
            
            snapshot = self.portfolio_analyzer.get_portfolio_snapshot()
            
            # Prepare data for alert manager
            portfolio_data = {
                'total_value': snapshot['total_value'],
                'total_profit_pct': snapshot['total_profit_pct'],
                'holdings': [
                    {
                        'coin': h['coin'],
                        'value': h['current_value'],
                        'profit_pct': h['profit_loss_pct']
                    }
                    for h in snapshot['holdings']
                ]
            }
            
            self.alert_manager.send_daily_summary(portfolio_data)
            print(f"{Fore.GREEN}✓ Daily summary sent{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error sending daily summary: {e}{Style.RESET_ALL}")
    
    def print_portfolio_report(self):
        """Print detailed portfolio report to console"""
        try:
            report = self.portfolio_analyzer.generate_summary_report()
            print(f"\n{Fore.CYAN}{report}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Error generating report: {e}{Style.RESET_ALL}")
    
    def run(self):
        """Start the monitoring service"""
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}MONITORING STARTED{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"\nMonitoring {len(config.CRYPTO_PAIRS)} cryptocurrencies")
        print(f"Profit targets: {config.PROFIT_TARGETS}%")
        print(f"Check interval: {config.PRICE_CHECK_INTERVAL_SECONDS} seconds")
        print(f"\n{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        # Send startup notification
        self.alert_manager.send_desktop_notification(
            "Luno Monitor Started",
            f"Monitoring {len(config.CRYPTO_PAIRS)} cryptocurrencies"
        )
        
        # Print initial report
        self.print_portfolio_report()
        
        # Schedule tasks
        schedule.every(config.PRICE_CHECK_INTERVAL_SECONDS).seconds.do(self.monitor_prices)
        schedule.every().day.at("09:00").do(self.daily_summary)
        schedule.every().hour.do(self.print_portfolio_report)
        
        # Run immediately
        self.monitor_prices()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")
            self.alert_manager.send_desktop_notification(
                "Luno Monitor Stopped",
                "Monitoring service has been stopped"
            )
            print(f"{Fore.GREEN}✓ Goodbye!{Style.RESET_ALL}\n")


def main():
    """Main entry point"""
    try:
        monitor = LunoPortfolioMonitor()
        monitor.run()
    except Exception as e:
        print(f"\n{Fore.RED}✗ Fatal error: {e}{Style.RESET_ALL}\n")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
