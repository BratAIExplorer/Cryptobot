"""
Cryptocurrency Dip Monitor
Alerts when target coins drop by specific percentages for buying opportunities
"""
import time
import requests
from datetime import datetime, timedelta
import json
import os
from src.alert_manager import AlertManager
import dip_monitor_config as dip_config

class DipMonitor:
    def __init__(self):
        self.alert_manager = AlertManager()
        self.watch_list = dip_config.DIP_WATCH_LIST
        self.alert_history = {}  # Track when alerts were sent
        self.price_highs = {}  # Track 24h highs
        self.start_time = datetime.now()
        self.state_file = 'dip_monitor_state.json'
        
        # Load previous state if exists
        self.load_state()
        
    def load_state(self):
        """Load previous monitoring state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.price_highs = state.get('price_highs', {})
                    print(f"✓ Loaded previous state with {len(self.price_highs)} baseline prices")
            except Exception as e:
                print(f"Could not load state: {e}")
    
    def save_state(self):
        """Save monitoring state"""
        try:
            state = {
                'price_highs': self.price_highs,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Could not save state: {e}")
    
    def get_price_coingecko(self, symbol):
        """Get current price from CoinGecko (fallback)"""
        try:
            # Map symbols to CoinGecko IDs
            gecko_ids = {
                'SOL': 'solana',
                'LINK': 'chainlink',
                'POL': 'polygon-ecosystem-token',
                'ETH': 'ethereum',
                'AVAX': 'avalanche-2'
            }
            
            coin_id = gecko_ids.get(symbol)
            if not coin_id:
                return None
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=myr"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data[coin_id]['myr']
            return None
        except Exception as e:
            print(f"CoinGecko error for {symbol}: {e}")
            return None
    
    def get_current_price(self, coin_data):
        """Get current price (try multiple sources)"""
        # Primary: CoinGecko (more reliable for these coins)
        price = self.get_price_coingecko(coin_data['symbol'])
        
        # Fallback: Use baseline
        if price is None:
            price = coin_data.get('baseline_price', 0)
            print(f"⚠️ Using baseline price for {coin_data['symbol']}")
        
        return price
    
    def update_baseline(self, symbol, current_price):
        """Update 24h high baseline"""
        if symbol not in self.price_highs:
            self.price_highs[symbol] = {
                'price': current_price,
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Update if current price is higher
            if current_price > self.price_highs[symbol]['price']:
                self.price_highs[symbol] = {
                    'price': current_price,
                    'timestamp': datetime.now().isoformat()
                }
                print(f"📈 New high for {symbol}: RM{current_price:,.2f}")
    
    def check_dip(self, symbol, coin_data):
        """Check if coin has dipped to alert thresholds"""
        current_price = self.get_current_price({'symbol': symbol, **coin_data})
        
        if current_price is None or current_price == 0:
            return
        
        # Update baseline
        if dip_config.USE_24H_HIGH_BASELINE:
            self.update_baseline(symbol, current_price)
            baseline = self.price_highs.get(symbol, {}).get('price', coin_data['baseline_price'])
        else:
            baseline = coin_data['baseline_price']
        
        # Calculate drop percentage
        drop_pct = ((baseline - current_price) / baseline) * 100
        
        # Check alert thresholds
        tier1 = coin_data['tier1_drop']
        tier2 = coin_data['tier2_drop']
        
        # Tier 2: Deep dip (20-30%)
        if drop_pct >= tier2:
            if not self.is_cooldown(symbol, 'tier2'):
                self.send_dip_alert(symbol, coin_data, current_price, baseline, drop_pct, tier=2)
                self.mark_alert_sent(symbol, 'tier2')
        
        # Tier 1: Moderate dip (10-15%)
        elif drop_pct >= tier1:
            if not self.is_cooldown(symbol, 'tier1'):
                self.send_dip_alert(symbol, coin_data, current_price, baseline, drop_pct, tier=1)
                self.mark_alert_sent(symbol, 'tier1')
    
    def is_cooldown(self, symbol, tier):
        """Check if alert is in cooldown period"""
        key = f"{symbol}_{tier}"
        if key not in self.alert_history:
            return False
        
        last_alert = self.alert_history[key]
        cooldown = timedelta(minutes=dip_config.ALERT_COOLDOWN_MINUTES)
        
        return datetime.now() - last_alert < cooldown
    
    def mark_alert_sent(self, symbol, tier):
        """Mark alert as sent"""
        key = f"{symbol}_{tier}"
        self.alert_history[key] = datetime.now()
    
    def send_dip_alert(self, symbol, coin_data, current_price, baseline, drop_pct, tier):
        """Send dip buying alert"""
        name = coin_data['name']
        
        if tier == 1:
            emoji = "💰"
            urgency = "BUYING OPPORTUNITY"
            recommendation = "Consider starting a position - 15% drop detected"
        else:  # tier == 2
            emoji = "🚨"
            urgency = "🔴 CRITICAL DIP ALERT"
            recommendation = "EXCEPTIONAL BUYING OPPORTUNITY - 50%+ crash detected! Research immediately and consider strong position"
        
        # Desktop notification
        title = f"{emoji} {name} Dip Alert!"
        message = f"{name} down {drop_pct:.1f}%! Now: RM{current_price:,.2f}"
        self.alert_manager.send_desktop_notification(title, message, timeout=15)
        
        # Email alert
        email_subject = f"{emoji} {urgency}: {name} ({symbol}) Down {drop_pct:.1f}%"
        email_body = f"""
<h2>{emoji} {name} Dip Alert - {urgency}</h2>

<p><strong>Coin:</strong> {name} ({symbol})</p>
<p><strong>Baseline Price:</strong> RM {baseline:,.2f}</p>
<p><strong>Current Price:</strong> RM {current_price:,.2f}</p>
<p><strong>Drop:</strong> <span style="color: red; font-size: 18px;">-{drop_pct:.2f}%</span></p>

<h3>💡 Recommendation:</h3>
<p>{recommendation}</p>

<h3>📊 Quick Actions:</h3>
<ul>
    <li>Check broader market sentiment (Bitcoin, Ethereum)</li>
    <li>Review recent news for {name}</li>
    <li>Consider your RM5,000 budget allocation</li>
    <li>Set limit buy orders if prices stabilize</li>
</ul>

<p><em>Alert sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        """
        self.alert_manager.send_email_alert(email_subject, email_body, is_html=True)
        
        # Telegram alert
        telegram_msg = f"""
{emoji} <b>{urgency}</b>

<b>{name} ({symbol})</b>
Baseline: RM{baseline:,.2f}
Current: <b>RM{current_price:,.2f}</b>
Drop: <b>-{drop_pct:.2f}%</b>

💡 <b>{recommendation}</b>

📍 Alert Tier: {tier} of 2
⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        self.alert_manager.send_telegram_alert(telegram_msg)
        
        print(f"\n{emoji} ALERT SENT: {name} down {drop_pct:.2f}% (Tier {tier})")
    
    def run(self):
        """Main monitoring loop"""
        end_time = self.start_time + timedelta(days=dip_config.MONITOR_DURATION_DAYS)
        
        print("=" * 60)
        print("🎯 DIP MONITOR STARTED")
        print("=" * 60)
        print(f"Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {dip_config.MONITOR_DURATION_DAYS} days")
        print(f"Check Interval: {dip_config.CHECK_INTERVAL_SECONDS}s")
        print("\nWatching:")
        for symbol, data in self.watch_list.items():
            print(f"  • {data['name']} ({symbol}): {data['tier1_drop']}% / {data['tier2_drop']}% drops")
        print("=" * 60)
        
        try:
            while datetime.now() < end_time:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking prices...")
                
                for symbol, coin_data in self.watch_list.items():
                    try:
                        self.check_dip(symbol, coin_data)
                    except Exception as e:
                        print(f"Error checking {symbol}: {e}")
                
                # Save state
                self.save_state()
                
                # Wait before next check
                time.sleep(dip_config.CHECK_INTERVAL_SECONDS)
        
        except KeyboardInterrupt:
            print("\n\n⏹️ Monitor stopped by user")
        
        print("\n" + "=" * 60)
        print("✅ DIP MONITOR ENDED")
        print("=" * 60)

if __name__ == '__main__':
    monitor = DipMonitor()
    monitor.run()
