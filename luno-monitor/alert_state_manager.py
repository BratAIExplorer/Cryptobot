"""
Persistent Alert State Manager
Helper class for main.py
"""
import json
import os
from datetime import datetime, timedelta

class AlertStateManager:
    """Manages persistent alert state with time-based cooldowns"""
    
    def __init__(self, state_file='alert_state.json'):
        self.state_file = state_file
        self.alerted_targets = {}
        self.cooldowns = {
            'profit_target': 24,  # 24 hours
            'price_drop': 2       # 2 hours
        }
        self.load_state()
    
    def load_state(self):
        """Load alert state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Convert ISO timestamps to datetime
                    for key, timestamp_str in data.items():
                        self.alerted_targets[key] = datetime.fromisoformat(timestamp_str)
            except Exception as e:
                print(f"⚠ Could not load alert state: {e}")
    
    def save_state(self):
        """Save alert state to file"""
        try:
            # Convert datetime to ISO for JSON
            data = {key: dt.isoformat() for key, dt in self.alerted_targets.items()}
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠ Could not save alert state: {e}")
    
    def is_allowed(self, alert_key, alert_type):
        """Check if enough time passed since last alert"""
        if alert_key not in self.alerted_targets:
            return True
        
        last_alert = self.alerted_targets[alert_key]
        cooldown_hours = self.cooldowns.get(alert_type, 24)
        time_passed = datetime.now() - last_alert
        
        return time_passed > timedelta(hours=cooldown_hours)
    
    def mark_sent(self, alert_key):
        """Mark alert as sent"""
        self.alerted_targets[alert_key] = datetime.now()
        self.save_state()
