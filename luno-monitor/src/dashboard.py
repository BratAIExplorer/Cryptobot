from flask import Flask, render_template, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime
import threading
import time
import subprocess
import sqlite3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

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
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(root_dir, 'data', 'trades_v3.db')
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
        # Check if we have recent validation data in database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'trades_v3.db')
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


@app.route('/cryptointel')
def cryptointel_dashboard():
    """CryptoIntel Hub - Unified Decision Dashboard"""
    return render_template('cryptointel_dashboard.html')


@app.route('/confluence')
def confluence_calculator():
    """Manual Confluence Score Calculator"""
    return render_template('confluence_calculator.html')


@app.route('/api/news/<symbol>')
def get_crypto_news(symbol):
    """Get top 5 critical news for a coin"""
    from src.news_filter import NewsFilter
    
    # Get API key from environment (optional)
    import os
    api_key = os.getenv('CRYPTOPANIC_API_KEY')  # Or use 'demo'
    
    filter = NewsFilter(api_key=api_key)
    news = filter.fetch_critical_news(symbol=symbol.upper(), max_items=5)
    formatted = filter.format_news_for_display(news)
    
    return jsonify({
        'symbol': symbol.upper(),
        'news_count': len(formatted),
        'news': formatted
    })



    return jsonify({
        'symbol': symbol.upper(),
        'news_count': len(formatted),
        'news': formatted
    })

@app.route('/api/veto_status')
def get_veto_status():
    """Get Status of the Veto Engine (Global & Per Coin)"""
    try:
        # Connect to V3 DB
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(root_dir, 'data', 'trades_v3.db')
        
        # Check if DB exists
        if not os.path.exists(db_path):
             return jsonify({'active_vetoes': [], 'btc_crash': False, 'status': 'V3 DB Not Found'})

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Fetch active vetoes (Active means lifted_at is NULL or in future)
        c.execute("SELECT rule_type, severity_level, reason, triggered_at FROM veto_events WHERE lifted_at IS NULL")
        rows = c.fetchall()
        
        vetoes = []
        for r in rows:
            vetoes.append({
                'rule': r[0],
                'level': r[1],
                'reason': r[2],
                'time': r[3]
            })
            
        conn.close()
        
        # Determine overall status
        status = "SAFE"
        if len(vetoes) > 0:
            status = "RESTRICTED"
            # specific check for crash
            for v in vetoes:
                if v['rule'] == 'BTC_CRASH' and v['level'] >= 3:
                     status = "CRASH MODE"
        
        return jsonify({
            'status': status,
            'active_vetoes': vetoes,
            'check_time': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/position_queue')
def get_position_queue():
    """Get positions requiring manual review (The 'Human Exits' Queue)"""
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(root_dir, 'data', 'trades_v3.db')
        
        if not os.path.exists(db_path):
             return jsonify({'queue': []})

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Logic for "Review Queue":
        # 1. Closed positions (for audit) - Limit 5
        # 2. Open positions that are "Stale" (>100 days) or "Underwater" (< -10%)
        # For MVP, we simply show ALL Open Positions with their PnL and Status
        
        # Get Open Positions
        c.execute("""
            SELECT id, symbol, strategy, entry_price, entry_date, 
                   current_price, unrealized_pnl_pct 
            FROM positions 
            WHERE status = 'OPEN' 
            ORDER BY entry_date ASC
        """)
        
        rows = c.fetchall()
        queue = []
        for r in rows:
            entry_date = r[4]
            # Calculate age
            try:
                # SQLite returns string for datetime
                dt = datetime.fromisoformat(entry_date)
            except:
                dt = datetime.now() # Fallback
            
            age_days = (datetime.utcnow() - dt).days
            
            # Determine "Review Urgent" status
            pnl_pct = r[6] if r[6] else 0.0
            urgency = "LOW"
            if age_days > 100: urgency = "HIGH (STALE)"
            if pnl_pct < -10.0: urgency = "HIGH (LOSS)"
            
            queue.append({
                'id': r[0],
                'symbol': r[1],
                'strategy': r[2],
                'price': r[3],
                'pnl_pct': pnl_pct,
                'age_days': age_days,
                'urgency': urgency
            })
            
        conn.close()
        return jsonify({'queue': queue, 'count': len(queue)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status_page():
    return render_template('status.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
