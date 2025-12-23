"""
CryptoIntel Hub - Confluence Scoring Engine V2
Multi-signal aggregation with regime detection and execution validation
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_coins import (CONFLUENCE_WEIGHTS, get_position_recommendation, 
                         get_coin_config, get_enabled_coins)

# Add core modules path for regime detection
core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'core')
sys.path.append(core_path)

try:
    from regime_detector import RegimeDetector, RegimeState
    from execution_validator import ExecutionValidator
    from signal_analyzer import SignalAnalyzer
    REGIME_ENABLED = True
except ImportError as e:
    print(f"Warning: Regime detector or Signal analyzer not available: {e}")
    REGIME_ENABLED = False


class ConfluenceEngine:
    """
    Aggregates multiple trading signals into unified decision score V2
    
    Signal Categories (100 points total):
    - Technical (30): RSI, MA crossovers, MACD, Volume
    - On-Chain (30): Whale holdings, exchange reserves, velocity, flow ratio  
    - Macro (20): BTC correlation, BTC price, risk regime, Fed rates
    - Fundamental (20): ETF inflows, sector rotation, model forecast
    
    New V2 Features:
    - Market Regime Detection (6 states: Bull/Bear/Transition/Undefined/Crisis)
    - Risk multipliers based on regime
    - Execution validation (slippage, liquidity)
    """
    
    def __init__(self, db_path=None, luno_db_path=None, exchange_client=None):
        if db_path is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(root_dir, 'data', 'trades.db')
        
        self.db_path = db_path
        
        self.exchange = exchange_client
        
        # V2 Components
        self.regime_detector = RegimeDetector(db_path) if REGIME_ENABLED else None
        self.execution_validator = ExecutionValidator(exchange_client) if REGIME_ENABLED else None
        self.signal_analyzer = SignalAnalyzer() if REGIME_ENABLED else None
        
        # Initialize confluence scores table
        self._init_database()
    
    def _init_database(self):
        """Create confluence_scores and market_regimes tables if not exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Original confluence scores table
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
                    raw_score INTEGER,
                    regime_state TEXT,
                    regime_multiplier REAL,
                    recommendation TEXT,
                    position_size TEXT,
                    stop_loss_pct REAL,
                    details TEXT,
                    exchange TEXT,
                    v1_score REAL
                )
            ''')
            
            # V2: Market regimes tracking table
            c.execute('''
                CREATE TABLE IF NOT EXISTS market_regimes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    regime_state TEXT,
                    confidence REAL,
                    btc_price REAL,
                    btc_ma50 REAL,
                    btc_ma200 REAL,
                    volatility_percentile REAL,
                    higher_highs BOOLEAN,
                    lower_lows BOOLEAN,
                    volume_trend TEXT,
                    recent_drawdown_pct REAL
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database init warning: {e}")

    def fetch_technicals(self, symbol: str, timeframe: str = '1h') -> Dict:
        """Fetch and calculate technical indicators from exchange"""
        if not self.execution_validator or not self.execution_validator.exchange:
            return {}
        
        try:
            exchange = self.execution_validator.exchange
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=250)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1+rs))
            
            # SMA
            df['sma50'] = df['close'].rolling(window=50).mean()
            df['sma200'] = df['close'].rolling(window=200).mean()
            
            # Volume Trend (Current vs 20-period avg)
            df['vol_ma'] = df['volume'].rolling(window=20).mean()
            
            if df.empty or len(df) < 2:
                return {}
                
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # MACD Proxy (Price vs EMA crossover)
            ema12 = df['close'].ewm(span=12, adjust=False).mean().iloc[-1]
            ema26 = df['close'].ewm(span=26, adjust=False).mean().iloc[-1]
            macd_signal = 'BULLISH' if ema12 > ema26 else 'BEARISH'
            
            return {
                'rsi': float(latest['rsi']),
                'price': float(latest['close']),
                'ma50': float(latest['sma50']),
                'ma200': float(latest['sma200']),
                'macd_signal': macd_signal,
                'volume_trend': 'INCREASING' if latest['volume'] > latest['vol_ma'] * 1.2 else 'STABLE'
            }
        except Exception as e:
            print(f"Error fetching technicals for {symbol}: {e}")
            return {}

    def get_automated_confluence_score(self, symbol: str, btc_df: Optional[pd.DataFrame] = None) -> Dict:
        """Fully automated confluence scoring for a symbol"""
        # 1. Fetch Technicals
        tech_inputs = self.fetch_technicals(symbol)
        
        # 2. Fetch Macro (Internal proxies + External APIs)
        macro_sentiment = self.fetch_market_sentiment()
        
        # 3. Combine into input dict
        inputs = {**tech_inputs}
        inputs['fear_and_greed'] = macro_sentiment.get('fear_and_greed', 50)
        
        # Mapping sentiment to internal fields
        fng = inputs['fear_and_greed']
        inputs['risk_regime'] = 'RISK-ON' if fng > 60 else ('RISK-OFF' if fng < 40 else 'MIXED')
        
        # BTC Price Proxy for Macro
        if btc_df is not None and not btc_df.empty:
             inputs['btc_price'] = btc_df.iloc[-1]['close']
             if 'close' in btc_df.columns:
                 ma50 = btc_df['close'].rolling(50).mean()
                 if not ma50.empty and not pd.isna(ma50.iloc[-1]):
                     inputs['btc_trend'] = 'BULLISH' if btc_df.iloc[-1]['close'] > ma50.iloc[-1] else 'BEARISH'
                 else:
                     inputs['btc_trend'] = 'NEUTRAL'
        
        return self.get_total_confluence_score(symbol, inputs, btc_df=btc_df)
    
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
        # DISABLED: Simple trend model shows POOR health (Win Rate <40%, MAPE >20%)
        # Re-enable when better forecast source is available (TradingView, CryptoQuant, or ML model)
        # For now, fundamental score = ETF flows + sector rotation only (15 points max)
        expected_return_pct = 0  # Disabled
        model_score = 0
        score += model_score
        breakdown['model_forecast'] = {
            'expected_return': expected_return_pct, 
            'score': model_score, 
            'max': 5,
            'status': 'DISABLED - awaiting better forecast model'
        }
        
        return {
            'score': score,
            'max_score': CONFLUENCE_WEIGHTS['fundamental'],
            'breakdown': breakdown
        }

    def _get_active_signals(self, manual_inputs: Dict) -> Dict[str, bool]:
        """Convert raw inputs to boolean active status for redundancy check"""
        active = {}
        
        # Momentum signals (threshold-based)
        rsi = manual_inputs.get('rsi', 50)
        active['rsi'] = rsi > 65 or rsi < 35
        
        # Trend signals
        price = manual_inputs.get('price', 0)
        ma200 = manual_inputs.get('ma200', 0)
        ma50 = manual_inputs.get('ma50', 0)
        if price and ma200:
            active['sma200'] = price > ma200
        if price and ma50:
            active['sma50'] = price > ma50
            
        # Volume
        vol_trend = manual_inputs.get('volume_trend', 'STABLE')
        active['volume_ma_ratio'] = vol_trend == 'INCREASING'
        
        # MACD
        macd = manual_inputs.get('macd_signal', 'NEUTRAL')
        active['macd'] = macd == 'BULLISH' or macd == 'BEARISH'
        
        return active
    
    def get_total_confluence_score(
        self, 
        symbol: str, 
        manual_inputs: Dict = None,
        btc_df: Optional[pd.DataFrame] = None,
        enable_regime_detection: bool = True
    ) -> Dict:
        """
        Calculate total confluence score from all signal categories (V2 with Regime Detection)
        
        Args:
            symbol: Coin symbol
            manual_inputs: Dict with all manual inputs for scoring
            btc_df: Bitcoin DataFrame for regime detection (needs 200+ candles)
            enable_regime_detection: Whether to apply regime-based risk multipliers
            
        Returns:
            Complete confluence analysis with recommendation and regime state
        """
        # Calculate all category scores (RAW scores 0-100)
        technical_raw = self.calculate_technical_score(symbol, manual_inputs)
        technical = technical_raw.copy()
        onchain = self.calculate_onchain_score(symbol, manual_inputs)
        macro = self.calculate_macro_score(symbol, manual_inputs)
        fundamental = self.calculate_fundamental_score(symbol, manual_inputs)
        
        # V1 Score (Base sum without penalties or regime)
        v1_score = (technical_raw['score'] + onchain['score'] + 
                   macro['score'] + fundamental['score'])
        
        # Total score
        total_score = (technical['score'] + onchain['score'] + 
                      macro['score'] + fundamental['score'])
        
        # V1 logic (for monitoring/calibration)
        v1_score = total_score
        
        # New V2: Signal Independence Analysis
        redundancy_penalty = 1.0
        if self.signal_analyzer:
            # Map inputs to active signals for analyzer
            active_signals = self._get_active_signals(manual_inputs)
            redundancy_penalty = self.signal_analyzer.get_redundancy_penalty(active_signals, manual_inputs)
            
            # Apply penalty to technical score (most prone to redundant indicators)
            if redundancy_penalty < 1.0:
                print(f"Applying redundancy penalty: {redundancy_penalty:.2f}x to technical score")
                technical['score'] = int(technical['score'] * redundancy_penalty)
                # Recalculate total
                total_score = (technical['score'] + onchain['score'] + 
                              macro['score'] + fundamental['score'])
        
        # Raw total score (before regime adjustment)
        raw_score = total_score
        
        # V2: Regime Detection & Risk Multiplier
        regime_state = None
        regime_confidence = 0.0
        regime_multiplier = 1.0
        regime_metrics = {}
        
        if enable_regime_detection and self.regime_detector and btc_df is not None and len(btc_df) >= 200:
            try:
                regime_state, regime_confidence, regime_metrics = self.regime_detector.detect_regime(btc_df)
                regime_multiplier = self.regime_detector.get_risk_multiplier(regime_state)
                
                # Save regime to database
                self._save_regime_state(regime_state, regime_confidence, regime_metrics)
                
            except Exception as e:
                print(f"Regime detection failed: {e}")
                regime_state = None
        
        # Final score with regime adjustment
        final_score = int(raw_score * regime_multiplier)
        
        # Get recommendation based on FINAL score
        recommendation = get_position_recommendation(final_score)
        
        # Add regime context to recommendation
        if regime_state:
            regime_name = regime_state.value if hasattr(regime_state, 'value') else str(regime_state)
            recommendation['regime_state'] = regime_name
            recommendation['regime_multiplier'] = regime_multiplier
            recommendation['regime_confidence'] = regime_confidence
        
        # Package results
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'scores': {
                'technical': technical,
                'onchain': onchain,
                'macro': macro,
                'fundamental': fundamental,
                'v1_total': v1_score,
                'raw_total': raw_score,
                'final_total': final_score,
                'max_possible': 100
            },
            'regime': {
                'state': regime_name if regime_state else 'NOT_DETECTED',
                'confidence': regime_confidence,
                'multiplier': regime_multiplier,
                'metrics': regime_metrics
            },
            'recommendation': recommendation
        }
        
        # Save to database
        self._save_confluence_score(result)
        
        return result
    
    def _save_regime_state(self, regime_state, confidence: float, metrics: Dict):
        """Save regime detection result to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            regime_name = regime_state.value if hasattr(regime_state, 'value') else str(regime_state)
            
            c.execute('''
                INSERT INTO market_regimes 
                (timestamp, regime_state, confidence, btc_price, btc_ma50, btc_ma200,
                 volatility_percentile, higher_highs, lower_lows, volume_trend, recent_drawdown_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                regime_name,
                confidence,
                metrics.get('btc_price', 0),
                metrics.get('btc_ma50', 0),
                metrics.get('btc_ma200', 0),
                metrics.get('volatility_percentile', 0),
                metrics.get('higher_highs', False),
                metrics.get('lower_lows', False),
                metrics.get('volume_trend', 'UNKNOWN'),
                metrics.get('recent_drawdown_pct', 0)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Could not save regime state: {e}")
    
    def _save_confluence_score(self, result: Dict):
        """Save confluence score to database (V2 with regime tracking)"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Extract regime info
            regime_state = result.get('regime', {}).get('state', 'NOT_DETECTED')
            regime_multiplier = result.get('regime', {}).get('multiplier', 1.0)
            
            # Extract values from nested dictionaries if necessary
            def get_score(val):
                if isinstance(val, dict): return val.get('score', 0)
                return val if val is not None else 0

            v1_score = result['scores'].get('v1_total')
            
            c.execute('''
                INSERT INTO confluence_scores 
                (timestamp, symbol, technical_score, onchain_score, macro_score, fundamental_score,
                 total_score, raw_score, regime_state, regime_multiplier, 
                 recommendation, position_size, stop_loss_pct, details, v1_score, exchange)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['timestamp'],
                result['symbol'],
                get_score(result['scores']['technical']),
                get_score(result['scores']['onchain']),
                get_score(result['scores']['macro']),
                get_score(result['scores']['fundamental']),
                result['scores']['final_total'],
                result['scores']['raw_total'],
                regime_state,
                regime_multiplier,
                result['recommendation']['rating'],
                result['recommendation']['position_size'],
                result['recommendation']['stop_loss_pct'],
                json.dumps(result),
                v1_score,
                getattr(self.exchange, 'exchange_name', 'UNKNOWN')
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
        regime = result.get('regime', {})
        
        print(f"\n{'='*60}")
        print(f"🎯 Confluence Analysis: {symbol}")
        print(f"{'='*60}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"\n📊 Signal Breakdown:")
        print(f"  Technical:   {scores['technical']['score']:2d}/{scores['technical']['max_score']} pts")
        print(f"  On-Chain:    {scores['onchain']['score']:2d}/{scores['onchain']['max_score']} pts")
        print(f"  Macro:       {scores['macro']['score']:2d}/{scores['macro']['max_score']} pts")
        print(f"  Fundamental: {scores['fundamental']['score']:2d}/{scores['fundamental']['max_score']} pts")
        
        # V2 Scoring display
        if 'final_total' in scores:
            print(f"\n📈 Market Regime: {regime.get('state', 'UNKNOWN')}")
            print(f"  Multiplier:   {regime.get('multiplier', 1.0)}x")
            print(f"  Raw Score:    {scores['raw_total']}/100")
            print(f"  Final Score:  {scores['final_total']}/100")
            display_score = scores['final_total']
        else:
            display_score = scores.get('total', 0)
            print(f"\n🎯 Total Score: {display_score}/100")
        
        # Visual bar
        bar_length = int(display_score * 0.4)  # 40 chars max
        bar = '█' * bar_length + '░' * (40 - bar_length)
        print(f"  [{bar}]")
        
        print(f"\n📍 Recommendation: {rec['rating']}")
        print(f"  Position Size: {rec['position_size']}")
        print(f"  Stop Loss: -{rec['stop_loss_pct']}%")
        
        # Reality Check Summary
        if 'execution' in result:
            exec_res = result['execution']
            print(f"\n⚡ Execution Reality Check:")
            print(f"  Status: {'✅ APPROVED' if exec_res.get('allowed') else '❌ REJECTED'}")
            if not exec_res.get('allowed'):
                print(f"  Reason: {exec_res.get('reason')}")
        
        print(f"{'='*60}\n")

    # --- API FETCH METHODS (V2 PRO) ---

    def fetch_onchain_from_glassnode(self, symbol: str) -> Dict:
        """
        Fetch real-world on-chain metrics from Glassnode
        Requires: GLASSNODE_API_KEY
        """
        api_key = os.getenv('GLASSNODE_API_KEY')
        if not api_key:
            return {}
            
        try:
            import requests
            # Mapping symbol to Glassnode asset
            asset = symbol.lower()
            
            # Example: Exchange Inflow Mean (7d)
            url = f"https://api.glassnode.com/v1/metrics/exchange/inflow_mean?a={asset}&m=7d&c=native&api_key={api_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                latest_val = data[-1]['v']
                # Heuristic: Compare vs 30d average (not fully implemented here)
                return {
                    'exchange_flow_ratio': round(latest_val, 4),
                    'whale_holdings': 50 # Placeholder if specific metric not hit
                }
            return {}
        except Exception as e:
            print(f"Error fetching Glassnode data: {e}")
            return {}

    def fetch_market_sentiment(self) -> Dict:
        """
        Fetch Fear & Greed Index and CryptoPanic News sentiment
        """
        results = {}
        
        # 1. CryptoPanic (Requires API Key)
        cp_key = os.getenv('CRYPTOPANIC_API_KEY')
        if cp_key:
            try:
                import requests
                url = f"https://cryptopanic.com/api/v1/posts/?auth_token={cp_key}&kind=news&filter=important"
                res_raw = requests.get(url, timeout=10)
                if res_raw.status_code == 200 and 'application/json' in res_raw.headers.get('Content-Type', ''):
                    res = res_raw.json()
                    # Aggregate sentiment from posts
                    upvotes = sum(p.get('votes', {}).get('positive', 0) for p in res.get('results', []))
                    downvotes = sum(p.get('votes', {}).get('negative', 0) for p in res.get('results', []))
                    
                    sentiment_ratio = 50
                    if (upvotes + downvotes) > 0:
                        sentiment_ratio = int((upvotes / (upvotes + downvotes)) * 100)
                    results['news_sentiment'] = sentiment_ratio
                else:
                    print(f"Warning: CryptoPanic returned response {res_raw.status_code}. Defaulting to neutral sentiment.")
                    results['news_sentiment'] = 50 # Balanced
            except Exception as e:
                print(f"Error fetching CryptoPanic: {e}. Defaulting to neutral.")
                results['news_sentiment'] = 50

        # 2. Alternative.me Fear & Greed (Free)
        try:
            import requests
            fng_res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
            results['fear_and_greed'] = int(fng_res['data'][0]['value'])
        except Exception:
            results['fear_and_greed'] = 50
            
        return results


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
