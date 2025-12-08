"""
CryptoIntel Hub - Confluence Scoring Engine
Multi-signal aggregation for trading decisions
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_coins import (CONFLUENCE_WEIGHTS, get_position_recommendation, 
                         get_coin_config, get_enabled_coins)


class ConfluenceEngine:
    """
    Aggregates multiple trading signals into unified decision score
    
    Signal Categories (100 points total):
    - Technical (30): RSI, MA crossovers, MACD, Volume
    - On-Chain (30): Whale holdings, exchange reserves, velocity, flow ratio  
    - Macro (20): BTC correlation, BTC price, risk regime, Fed rates
    - Fundamental (20): ETF inflows, sector rotation, model forecast
    """
    
    def __init__(self, db_path=None, luno_db_path=None):
        if db_path is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(root_dir, 'data', 'trades.db')
        
        self.db_path = db_path
        
        # Initialize confluence scores table
        self._init_database()
    
    def _init_database(self):
        """Create confluence_scores table if not exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS confluence_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    symbol TEXT,
                    technical_score INTEGER,
                    onchain_score INTEGER,
                    macro_score INTEGER,
                    fundamental_score INTEGER,
                    total_score INTEGER,
                    recommendation TEXT,
                    position_size TEXT,
                    stop_loss_pct REAL,
                    details TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database init warning: {e}")
    
    def calculate_technical_score(self, symbol: str, manual_inputs: Dict = None) -> Dict:
        """
        Calculate technical analysis score (0-30 points)
        
        Signals:
        - RSI (5 points): 40-70 = healthy range
        - MA Crossover (10 points): Price > MA50 and MA200
        - MACD (8 points): Bullish signal
        - Volume Trend (7 points): Increasing volume
        
        Args:
            symbol: Coin symbol
            manual_inputs: Optional dict with {rsi, macd_signal, volume_trend, price, ma50, ma200}
        """
        score = 0
        breakdown = {}
        
        if manual_inputs is None:
            manual_inputs = {}
        
        # RSI Score (0-5 points)
        rsi = manual_inputs.get('rsi', 50)
        if 40 <= rsi <= 70:
            rsi_score = 5
        elif 30 <= rsi < 40 or 70 < rsi <= 80:
            rsi_score = 3
        else:
            rsi_score = 0
        score += rsi_score
        breakdown['rsi'] = {'value': rsi, 'score': rsi_score, 'max': 5}
        
        # MA Crossover (0-10 points)
        price = manual_inputs.get('price', 0)
        ma50 = manual_inputs.get('ma50', 0)
        ma200 = manual_inputs.get('ma200', 0)
        
        ma_score = 0
        if price > 0 and ma50 > 0:
            if price > ma50:
                ma_score += 5
            if price > ma200:
                ma_score += 5
        score += ma_score
        breakdown['ma_crossover'] = {'score': ma_score, 'max': 10}
        
        # MACD Score (0-8 points)
        macd_signal = manual_inputs.get('macd_signal', 'NEUTRAL').upper()
        macd_score = {'BULLISH': 8, 'NEUTRAL': 4, 'BEARISH': 0}.get(macd_signal, 0)
        score += macd_score
        breakdown['macd'] = {'signal': macd_signal, 'score': macd_score, 'max': 8}
        
        # Volume Trend (0-7 points)
        volume_trend = manual_inputs.get('volume_trend', 'STABLE').upper()
        volume_score = {'INCREASING': 7, 'STABLE': 3, 'DECREASING': 0}.get(volume_trend, 0)
        score += volume_score
        breakdown['volume'] = {'trend': volume_trend, 'score': volume_score, 'max': 7}
        
        return {
            'score': score,
            'max_score': CONFLUENCE_WEIGHTS['technical'],
            'breakdown': breakdown
        }
    
    def calculate_onchain_score(self, symbol: str, manual_inputs: Dict = None) -> Dict:
        """
        Calculate on-chain metrics score (0-30 points)
        
        Signals:
        - Whale Holdings (8 points): High accumulation = bullish
        - Exchange Reserves (8 points): Low reserves = supply squeeze
        - Velocity (6 points): High activity = interest
        - Exchange Flow Ratio (8 points): Low = whales not selling
        
        Args:
            symbol: Coin symbol
            manual_inputs: Optional dict with onchain metrics
        """
        score = 0
        breakdown = {}
        
        if manual_inputs is None:
            manual_inputs = {}
        
        # Whale Holdings (0-8 points)
        # For XRP: >45B = 7-year high (bullish)
        whale_holdings = manual_inputs.get('whale_holdings', 0)
        whale_threshold = {'XRP': 45, 'BTC': 0.008, 'ETH': 0.12}.get(symbol, 0)  # % of supply
        
        if whale_holdings >= whale_threshold * 1.05:  # 5% above threshold
            whale_score = 8
        elif whale_holdings >= whale_threshold:
            whale_score = 6
        elif whale_holdings >= whale_threshold * 0.95:
            whale_score = 4
        else:
            whale_score = 0
        score += whale_score
        breakdown['whale_holdings'] = {'value': whale_holdings, 'score': whale_score, 'max': 8}
        
        # Exchange Reserves (0-8 points)
        # Lower = bullish (supply squeeze)
        exchange_reserves = manual_inputs.get('exchange_reserves', 5)
        if exchange_reserves < 2.5:
            reserves_score = 8
        elif exchange_reserves < 3.0:
            reserves_score = 6
        elif exchange_reserves < 4.0:
            reserves_score = 4
        else:
            reserves_score = 0
        score += reserves_score
        breakdown['exchange_reserves'] = {'value': exchange_reserves, 'score': reserves_score, 'max': 8}
        
        # Velocity (0-6 points)
        velocity = manual_inputs.get('velocity', 0.02)
        if velocity > 0.030:
            velocity_score = 6
        elif velocity > 0.020:
            velocity_score = 4
        else:
            velocity_score = 2
        score += velocity_score
        breakdown['velocity'] = {'value': velocity, 'score': velocity_score, 'max': 6}
        
        # Exchange Flow Ratio (0-8 points)
        # Low ratio = whales holding, not dumping
        flow_ratio = manual_inputs.get('exchange_flow_ratio', 0.5)
        if flow_ratio < 0.10:
            flow_score = 8
        elif flow_ratio < 0.30:
            flow_score = 6
        elif flow_ratio < 0.50:
            flow_score = 4
        else:
            flow_score = 0
        score += flow_score
        breakdown['flow_ratio'] = {'value': flow_ratio, 'score': flow_score, 'max': 8}
        
        # Dormant Circulation Penalty
        dormant_circulation = manual_inputs.get('dormant_circulation', 'MEDIUM').upper()
        if dormant_circulation == 'HIGH':
            score = max(0, score - 8)  # Bearish signal
            breakdown['dormant_penalty'] = {'level': dormant_circulation, 'penalty': -8}
        
        return {
            'score': min(score, CONFLUENCE_WEIGHTS['onchain']),  # Cap at max
            'max_score': CONFLUENCE_WEIGHTS['onchain'],
            'breakdown': breakdown
        }
    
    def calculate_macro_score(self, symbol: str, manual_inputs: Dict = None) -> Dict:
        """
        Calculate macro environment score (0-20 points)
        
        Signals:
        - BTC Trend (8 points): Market leader direction
        - BTC Price Threshold (5 points): >$95k = strong market
        - Risk Regime (5 points): RISK-ON = favorable
        - Fed Rate Cuts (2 points): Easing = bullish for crypto
        
        Args:
            symbol: Coin symbol
            manual_inputs: Optional dict with macro metrics
        """
        score = 0
        breakdown = {}
        
        if manual_inputs is None:
            manual_inputs = {}
        
        # BTC Trend (0-8 points)
        btc_trend = manual_inputs.get('btc_trend', 'NEUTRAL').upper()
        btc_trend_score = {'BULLISH': 8, 'CONSOLIDATING': 4, 'BEARISH': 0}.get(btc_trend, 0)
        score += btc_trend_score
        breakdown['btc_trend'] = {'trend': btc_trend, 'score': btc_trend_score, 'max': 8}
        
        # BTC Price Threshold (0-5 points)
        btc_price = manual_inputs.get('btc_price', 90000)
        if btc_price > 95000:
            btc_price_score = 5
        elif btc_price > 90000:
            btc_price_score = 3
        else:
            btc_price_score = 0
        score += btc_price_score
        breakdown['btc_price'] = {'price': btc_price, 'score': btc_price_score, 'max': 5}
        
        # Risk Regime (0-5 points)
        risk_regime = manual_inputs.get('risk_regime', 'MIXED').upper()
        risk_score = {'RISK-ON': 5, 'MIXED': 2, 'RISK-OFF': 0}.get(risk_regime, 0)
        score += risk_score
        breakdown['risk_regime'] = {'regime': risk_regime, 'score': risk_score, 'max': 5}
        
        # Fed Rate Cuts (0-2 points)
        fed_rate_prob = manual_inputs.get('fed_rate_cut_prob', 50)
        if fed_rate_prob > 80:
            fed_score = 2
        elif fed_rate_prob > 60:
            fed_score = 1
        else:
            fed_score = 0
        score += fed_score
        breakdown['fed_rates'] = {'probability': fed_rate_prob, 'score': fed_score, 'max': 2}
        
        return {
            'score': score,
            'max_score': CONFLUENCE_WEIGHTS['macro'],
            'breakdown': breakdown
        }
    
    def calculate_fundamental_score(self, symbol: str, manual_inputs: Dict = None) -> Dict:
        """
        Calculate fundamental analysis score (0-20 points)
        
        Signals:
        - ETF Inflows (8 points): Institutional demand
        - Sector Rotation (7 points): XLM/ADA leading = XRP follows
        - Model Forecast (5 points): Positive expected value
        
        Args:
            symbol: Coin symbol
            manual_inputs: Optional dict with fundamental metrics
        """
        score = 0
        breakdown = {}
        
        if manual_inputs is None:
            manual_inputs = {}
        
        # ETF Inflows (0-8 points)
        etf_inflows = manual_inputs.get('etf_inflows', 0)  # Million USD
        if etf_inflows > 400:
            etf_score = 8
        elif etf_inflows > 200:
            etf_score = 5
        elif etf_inflows > 50:
            etf_score = 3
        else:
            etf_score = 0
        score += etf_score
        breakdown['etf_inflows'] = {'value': etf_inflows, 'score': etf_score, 'max': 8}
        
        # Sector Rotation (0-7 points)
        # Check if similar coins (XLM for XRP) are outperforming
        xlm_gain = manual_inputs.get('xlm_outperformance_pct', 0)  # % gain vs baseline
        if xlm_gain > 15:
            sector_score = 7
        elif xlm_gain > 10:
            sector_score = 5
        elif xlm_gain > 5:
            sector_score = 3
        else:
            sector_score = 0
        score += sector_score
        breakdown['sector_rotation'] = {'xlm_outperformance': xlm_gain, 'score': sector_score, 'max': 7}
        
        # Model Forecast (0-5 points)
        # Check if model predicts positive expected value
        expected_return_pct = manual_inputs.get('model_expected_return', 0)
        if expected_return_pct > 10:
            model_score = 5
        elif expected_return_pct > 5:
            model_score = 4
        elif expected_return_pct > 0:
            model_score = 3
        else:
            model_score = 0
        score += model_score
        breakdown['model_forecast'] = {'expected_return': expected_return_pct, 'score': model_score, 'max': 5}
        
        return {
            'score': score,
            'max_score': CONFLUENCE_WEIGHTS['fundamental'],
            'breakdown': breakdown
        }
    
    def get_total_confluence_score(self, symbol: str, manual_inputs: Dict = None) -> Dict:
        """
        Calculate total confluence score from all signal categories
        
        Args:
            symbol: Coin symbol
            manual_inputs: Dict with all manual inputs for scoring
            
        Returns:
            Complete confluence analysis with recommendation
        """
        # Calculate all category scores
        technical = self.calculate_technical_score(symbol, manual_inputs)
        onchain = self.calculate_onchain_score(symbol, manual_inputs)
        macro = self.calculate_macro_score(symbol, manual_inputs)
        fundamental = self.calculate_fundamental_score(symbol, manual_inputs)
        
        # Total score
        total_score = (technical['score'] + onchain['score'] + 
                      macro['score'] + fundamental['score'])
        
        # Get recommendation
        recommendation = get_position_recommendation(total_score)
        
        # Package results
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'scores': {
                'technical': technical,
                'onchain': onchain,
                'macro': macro,
                'fundamental': fundamental,
                'total': total_score,
                'max_possible': 100
            },
            'recommendation': recommendation
        }
        
        # Save to database
        self._save_confluence_score(result)
        
        return result
    
    def _save_confluence_score(self, result: Dict):
        """Save confluence score to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO confluence_scores 
                (timestamp, symbol, technical_score, onchain_score, macro_score, fundamental_score,
                 total_score, recommendation, position_size, stop_loss_pct, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['timestamp'],
                result['symbol'],
                result['scores']['technical']['score'],
                result['scores']['onchain']['score'],
                result['scores']['macro']['score'],
                result['scores']['fundamental']['score'],
                result['scores']['total'],
                result['recommendation']['rating'],
                result['recommendation']['position_size'],
                result['recommendation']['stop_loss_pct'],
                str(result['scores'])  # Store full breakdown as JSON string
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Could not save confluence score: {e}")
    
    def print_confluence_report(self, result: Dict):
        """Print formatted confluence score report"""
        symbol = result['symbol']
        scores = result['scores']
        rec = result['recommendation']
        
        print(f"\n{'='*60}")
        print(f"🎯 Confluence Analysis: {symbol}")
        print(f"{'='*60}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"\n📊 Signal Breakdown:")
        print(f"  Technical:   {scores['technical']['score']:2d}/{scores['technical']['max_score']} pts")
        print(f"  On-Chain:    {scores['onchain']['score']:2d}/{scores['onchain']['max_score']} pts")
        print(f"  Macro:       {scores['macro']['score']:2d}/{scores['macro']['max_score']} pts")
        print(f"  Fundamental: {scores['fundamental']['score']:2d}/{scores['fundamental']['max_score']} pts")
        print(f"\n🎯 Total Score: {scores['total']}/100")
        
        # Visual bar
        bar_length = int(scores['total'] * 0.4)  # 40 chars max
        bar = '█' * bar_length + '░' * (40 - bar_length)
        print(f"  [{bar}]")
        
        print(f"\n📍 Recommendation: {rec['rating']}")
        print(f"  Position Size: {rec['position_size']}")
        print(f"  Stop Loss: -{rec['stop_loss_pct']}%")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    # Test the confluence engine
    engine = ConfluenceEngine()
    
    # Sample manual inputs (in production, these come from APIs/dashboard)
    test_inputs = {
        'rsi': 62,
        'macd_signal': 'BULLISH',
        'volume_trend': 'INCREASING',
        'price': 2.00,
        'ma50': 1.85,
        'ma200': 1.45,
        'whale_holdings': 48,
        'exchange_reserves': 2.6,
        'velocity': 0.0324,
        'exchange_flow_ratio': 0.98,
        'dormant_circulation': 'HIGH',
        'btc_trend': 'CONSOLIDATING',
        'btc_price': 96800,
        'risk_regime': 'RISK-ON',
        'fed_rate_cut_prob': 87,
        'etf_inflows': 439,
        'xlm_outperformance_pct': 12,
        'model_expected_return': 8.5
    }
    
    result = engine.get_total_confluence_score('XRP', test_inputs)
    engine.print_confluence_report(result)
