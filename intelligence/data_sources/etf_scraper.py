import json
import os
from datetime import datetime

class ETFScraper:
    """
    Manager for ETF Inflow Data.
    Since no free public API exists for real-time ETF flows, this module act as:
    1. A persistent storage (JSON) for manual inputs.
    2. A structured interface for the Scorer to read 'Current ETF Status'.
    """
    
    def __init__(self):
        # Path to storage file
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.cache_file = os.path.join(self.data_dir, "etf_flows.json")
        
        # Ensure dir exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Ensure file exists
        if not os.path.exists(self.cache_file):
            self._save_data({})

    def get_etf_status(self, symbol):
        """
        Returns (score_modifier, reason_string) based on stored flow data.
        """
        data = self._load_data()
        
        # Default empty data
        asset_data = data.get(symbol.upper(), {'status': 'NONE', 'flows_7d': 0})
        
        if asset_data['status'] == 'APPROVED':
            return 10.0, "ETF Approved & Trading" # Base points for having one
        elif asset_data['status'] == 'FILING_ACTIVE':
            return 5.0, "ETF Filings Review Active"
        elif asset_data['status'] == 'RUMORS':
            return 2.0, "Credible Rumors"
        else:
            return 0.0, "No ETF Data"

    def update_etf_status(self, symbol, status, weekly_inflow_m=0):
        """
        Manually update the status for an asset.
        status: APPROVED, FILING_ACTIVE, RUMORS, NONE
        """
        data = self._load_data()
        
        data[symbol.upper()] = {
            'status': status,
            'flows_7d': weekly_inflow_m,
            'last_updated': datetime.now().isoformat()
        }
        
        self._save_data(data)
        print(f"✅ Updated ETF Status for {symbol}: {status}")

    def _load_data(self):
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_data(self, data):
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=4)

if __name__ == "__main__":
    # Test / Setup Initial Data
    scraper = ETFScraper()
    
    # Initialize baseline for key assets
    scraper.update_etf_status("BTC", "APPROVED", 1500)
    scraper.update_etf_status("ETH", "APPROVED", -200)
    scraper.update_etf_status("XRP", "FILING_ACTIVE", 0)
    scraper.update_etf_status("SOL", "FILING_ACTIVE", 0)
    
    print("\nState Dump:")
    print(scraper._load_data())
