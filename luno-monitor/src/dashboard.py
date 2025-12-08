from flask import Flask, render_template, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime
import threading
import time
import subprocess
import sqlite3

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.portfolio_analyzer import PortfolioAnalyzer
from src.price_monitor import PriceMonitor
from src.luno_client import LunoClient
from src.model_validator import ModelValidator
from src.confluence_engine import ConfluenceEngine
import config
import config_coins

app = Flask(__name__)
CORS(app)

# Initialize components
analyzer = PortfolioAnalyzer()
monitor = PriceMonitor()
luno_client = LunoClient()
model_validator = ModelValidator()
confluence_engine = ConfluenceEngine()

# Global cache for data
data_cache = {
    'last_update': None,
    'portfolio': None,
    'prices': {},
    'sentiment': {}
}

def update_data_background():
    """Background task to update data periodically"""
    while True:
        try:
            # Update portfolio snapshot
            snapshot = analyzer.get_portfolio_snapshot()
            data_cache['portfolio'] = snapshot
            data_cache['last_update'] = datetime.now()
            
            # Update prices
            data_cache['prices'] = monitor.get_all_prices()
            
            # Update sentiment (mock for now, or fetch from CoinGecko)
            # In a real app, we'd fetch this less frequently to avoid rate limits
            
        except Exception as e:
            print(f"Error updating dashboard data: {e}")
            
        time.sleep(60)  # Update every minute

# Start background thread
update_thread = threading.Thread(target=update_data_background, daemon=True)
update_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

import json

# ... (existing imports)

@app.route('/api/data')
def get_data():
    # If cache is empty, fetch immediately
    if data_cache['portfolio'] is None:
        data_cache['portfolio'] = analyzer.get_portfolio_snapshot()
        data_cache['prices'] = monitor.get_all_prices()
        data_cache['last_update'] = datetime.now()
    
    # Load events
    events = []
    try:
        events_path = os.path.join(os.path.dirname(__file__), 'data', 'events.json')
        if os.path.exists(events_path):
            with open(events_path, 'r') as f:
                events = json.load(f)
    except Exception as e:
        print(f"Error loading events: {e}")

    return jsonify({
        'portfolio': data_cache['portfolio'],
        'prices': data_cache['prices'],
        'events': events,
        'last_update': data_cache['last_update'].isoformat() if data_cache['last_update'] else None
    })

@app.route('/api/transactions/<coin>')
def get_transactions(coin):
    """Get transaction history for a specific coin"""
    try:
        # Find account ID
        accounts = luno_client.get_all_accounts()
        account_id = next((a['account_id'] for a in accounts if a['asset'] == coin), None)
        
        if not account_id:
            return jsonify({'error': 'Account not found'}), 404
            
        transactions = luno_client.get_transactions(account_id, min_row=-50, max_row=0)
        return jsonify({'transactions': transactions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot_status')
def get_bot_status():
    """Get status of all bot services"""
    services = [
        'crypto_bot_runner.service',
        'portfolio_monitor.service',
        'dip_monitor.service',
        'crypto_bot.service'
    ]
    
    status = {}
    for service in services:
        try:
            # Check systemd status
            cmd = f"sudo /usr/bin/systemctl is-active {service}"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            is_active = result.stdout.strip() == 'active'
            
            # Clean name
            name = service.replace('.service', '').replace('_', ' ').title()
            status[service] = {
                'name': name,
                'active': is_active,
                'status': 'RUNNING' if is_active else 'STOPPED'
            }
        except Exception as e:
            status[service] = {'name': service, 'active': False, 'status': 'ERROR'}
    # Get trading stats from DB
    try:
        # Auto-detect path (works locally and on VPS)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(root_dir, 'data', 'trades.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN'")
        open_positions = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM trades")
        total_trades = c.fetchone()[0]
        
        conn.close()
    except:
        open_positions = 0
        total_trades = 0
        
    return jsonify({
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'services': status,
        'stats': {
            'open_positions': open_positions,
            'total_trades': total_trades
        }
    })


@app.route('/api/model_health')
def get_model_health():
    """Get model validation status for all tracked coins"""
    try:
        results = {}
        enabled_coins = config_coins.get_enabled_coins()
        
        # Check if we have recent validation data in database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'trades.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        for symbol in enabled_coins:
            c.execute('''
                SELECT mape, win_rate, sharpe_ratio, health_status, validation_date
                FROM model_validation
                WHERE symbol = ?
                ORDER BY validation_date DESC
                LIMIT 1
            ''', (symbol,))
            row = c.fetchone()
            
            if row:
                results[symbol] = {
                    'mape': row[0],
                    'win_rate': row[1],
                    'sharpe_ratio': row[2],
                    'health_status': row[3],
                    'last_validation': row[4]
                }
            else:
                results[symbol] = {
                    'health_status': 'NOT_VALIDATED',
                    'message': 'Run validation first'
                }
        
        conn.close()
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/confluence_score/<symbol>')
def get_confluence_score(symbol):
    """Get confluence score for a specific coin"""
    try:
        # In production, manual_inputs would come from UI form or APIs
        # For now, return structure for frontend to populate
        return jsonify({
            'symbol': symbol,
            'status': 'ready',
            'message': 'Submit manual inputs via POST to calculate score',
            'required_inputs': {
                'technical': ['rsi', 'macd_signal', 'volume_trend', 'price', 'ma50', 'ma200'],
                'onchain': ['whale_holdings', 'exchange_reserves', 'velocity', 'exchange_flow_ratio', 'dormant_circulation'],
                'macro': ['btc_trend', 'btc_price', 'risk_regime', 'fed_rate_cut_prob'],
                'fundamental': ['etf_inflows', 'xlm_outperformance_pct', 'model_expected_return']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tracked_coins')
def get_tracked_coins():
    """Get list of all tracked coins with configuration"""
    return jsonify({
        'coins': config_coins.TRACKED_COINS,
        'enabled_coins': config_coins.get_enabled_coins()
    })



@app.route('/status')
def status_page():
    return render_template('status.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
