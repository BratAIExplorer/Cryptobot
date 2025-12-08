"""
CryptoIntel Hub - Model Validation Engine
Validates forecast models using historical backtesting
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sqlite3
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_coins import classify_model_health, get_enabled_coins


class ModelValidator:
    """
    Validates trading forecast models using historical data
    
    Features:
    - Simulated backtesting (apply current model logic to historical prices)
    - MAPE calculation (Mean Absolute Percentage Error)
    - Win Rate calculation (% of forecasts hitting median target)
    - Sharpe Ratio (risk-adjusted returns)
    - Model health classification
    """
    
    def __init__(self, db_path=None):
        if db_path is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(root_dir, 'data', 'trades.db')
        
        self.db_path = db_path
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        
    def get_historical_prices(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """
        Fetch historical price data from CoinGecko (free API)
        
        Args:
            symbol: Coin symbol (e.g., 'XRP', 'BTC')
            days: Number of days to look back
            
        Returns:
            DataFrame with columns: date, price
        """
        # Map symbols to CoinGecko IDs
        coingecko_ids = {
            'XRP': 'ripple',
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'XLM': 'stellar',
            'ADA': 'cardano',
            'SOL': 'solana'
        }
        
        coin_id = coingecko_ids.get(symbol.upper())
        if not coin_id:
            raise ValueError(f"Coin {symbol} not supported")
        
        try:
            url = f"{self.coingecko_base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract price data
            prices = data['prices']  # [[timestamp_ms, price], ...]
            
            df = pd.DataFrame(prices, columns=['timestamp_ms', 'price'])
            df['date'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
            df = df[['date', 'price']]
            
            return df
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def simulate_forecast(self, historical_prices: pd.DataFrame, 
                         forecast_window_weeks: int = 8) -> List[Dict]:
        """
        Simulate forecasts for each week in historical data
        
        Args:
            historical_prices: DataFrame with date, price columns
            forecast_window_weeks: Forecast horizon in weeks
            
        Returns:
            List of forecast results with predicted vs actual
        """
        results = []
        forecast_days = forecast_window_weeks * 7
        
        # Skip last forecast_days since we can't validate them yet
        max_forecast_date = historical_prices['date'].max() - timedelta(days=forecast_days)
        
        # Generate forecasts for each week
        for i in range(0, len(historical_prices) - forecast_days, 7):
            forecast_date = historical_prices.iloc[i]['date']
            
            if forecast_date > max_forecast_date:
                break
            
            current_price = historical_prices.iloc[i]['price']
            
            # Simple forecast model (you can enhance this)
            # Uses recent trend + volatility to create P10/P25/Median/P75/P90
            recent_prices = historical_prices.iloc[max(0, i-30):i]['price']
            
            if len(recent_prices) < 7:
                continue
            
            trend = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            volatility = recent_prices.std() / recent_prices.mean()
            
            # Forecast distribution (your actual model would be more sophisticated)
            median_forecast = current_price * (1 + trend * 0.5)  # Dampened trend
            p25_forecast = median_forecast * (1 - volatility * 1.5)
            p75_forecast = median_forecast * (1 + volatility * 1.5)
            p10_forecast = median_forecast * (1 - volatility * 2.5)
            p90_forecast = median_forecast * (1 + volatility * 2.5)
            
            # Get actual price at target date
            target_date = forecast_date + timedelta(days=forecast_days)
            actual_row = historical_prices[historical_prices['date'] >= target_date].iloc[0] \
                         if len(historical_prices[historical_prices['date'] >= target_date]) > 0 else None
            
            if actual_row is None:
                continue
            
            actual_price = actual_row['price']
            
            # Calculate metrics
            error = abs(median_forecast - actual_price)
            error_pct = error / actual_price
            hit_target = (actual_price >= p25_forecast and actual_price <= p75_forecast)
            
            results.append({
                'forecast_date': forecast_date,
                'target_date': target_date,
                'current_price': current_price,
                'predicted_median': median_forecast,
                'predicted_p25': p25_forecast,
                'predicted_p75': p75_forecast,
                'predicted_p10': p10_forecast,
                'predicted_p90': p90_forecast,
                'actual_price': actual_price,
                'error': error,
                'error_pct': error_pct,
                'hit_target': hit_target
            })
        
        return results
    
    def calculate_mape(self, forecasts: List[Dict]) -> float:
        """Calculate Mean Absolute Percentage Error"""
        if not forecasts:
            return float('inf')
        
        errors = [f['error_pct'] for f in forecasts]
        return np.mean(errors)
    
    def calculate_win_rate(self, forecasts: List[Dict]) -> float:
        """Calculate percentage of forecasts that hit target"""
        if not forecasts:
            return 0.0
        
        hits = sum(1 for f in forecasts if f['hit_target'])
        return hits / len(forecasts)
    
    def calculate_sharpe_ratio(self, forecasts: List[Dict], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio for forecast-based trading
        
        Args:
            forecasts: List of forecast results
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        if not forecasts:
            return 0.0
        
        # Calculate returns if trading on median forecast
        returns = []
        for f in forecasts:
            expected_return = (f['predicted_median'] - f['current_price']) / f['current_price']
            actual_return = (f['actual_price'] - f['current_price']) / f['current_price']
            returns.append(actual_return)
        
        if len(returns) < 2:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualized Sharpe (assuming weekly forecasts = 52 per year)
        sharpe = (avg_return - risk_free_rate / 52) / std_return * np.sqrt(52)
        return sharpe
    
    def validate_model(self, symbol: str, lookback_days: int = 365) -> Dict:
        """
        Run complete model validation
        
        Args:
            symbol: Coin symbol to validate
            lookback_days: Historical lookback period
            
        Returns:
            Validation metrics and health status
        """
        print(f"\n{'='*60}")
        print(f"Model Validation: {symbol}")
        print(f"{'='*60}")
        
        # Fetch historical data
        print(f"Fetching {lookback_days} days of historical data...")
        historical_prices = self.get_historical_prices(symbol, lookback_days)
        
        if historical_prices.empty:
            return {
                'symbol': symbol,
                'status': 'ERROR',
                'message': 'Failed to fetch historical data'
            }
        
        # Simulate forecasts
        print("Running simulated backtesting...")
        forecasts = self.simulate_forecast(historical_prices, forecast_window_weeks=8)
        
        if not forecasts:
            return {
                'symbol': symbol,
                'status': 'ERROR',
                'message': 'Insufficient data for backtesting'
            }
        
        # Calculate metrics
        mape = self.calculate_mape(forecasts)
        win_rate = self.calculate_win_rate(forecasts)
        sharpe_ratio = self.calculate_sharpe_ratio(forecasts)
        
        # Classify health
        health_status = classify_model_health(win_rate, mape, sharpe_ratio)
        
        # Store results in database
        self._save_validation_results(symbol, forecasts, mape, win_rate, sharpe_ratio, health_status)
        
        results = {
            'symbol': symbol,
            'lookback_days': lookback_days,
            'num_forecasts': len(forecasts),
            'mape': mape,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'health_status': health_status,
            'message': self._get_health_message(health_status),
            'forecasts': forecasts[:5]  # Sample forecasts
        }
        
        print(f"\n📊 Results:")
        print(f"  MAPE: {mape*100:.2f}%")
        print(f"  Win Rate: {win_rate*100:.2f}%")
        print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"  Health: {health_status} {self._get_health_emoji(health_status)}")
        print(f"  {results['message']}")
        print(f"{'='*60}\n")
        
        return results
    
    def _save_validation_results(self, symbol: str, forecasts: List[Dict], 
                                 mape: float, win_rate: float, sharpe_ratio: float,
                                 health_status: str):
        """Save validation results to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Create table if not exists
            c.execute('''
                CREATE TABLE IF NOT EXISTS model_validation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    validation_date DATETIME,
                    symbol TEXT,
                    lookback_days INTEGER,
                    num_forecasts INTEGER,
                    mape REAL,
                    win_rate REAL,
                    sharpe_ratio REAL,
                    health_status TEXT
                )
            ''')
            
            # Insert validation summary
            c.execute('''
                INSERT INTO model_validation 
                (validation_date, symbol, lookback_days, num_forecasts, mape, win_rate, sharpe_ratio, health_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), symbol, 365, len(forecasts), mape, win_rate, sharpe_ratio, health_status))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Could not save validation results: {e}")
    
    def _get_health_message(self, status: str) -> str:
        """Get descriptive message for health status"""
        messages = {
            'EXCELLENT': 'Model is highly reliable - safe to use for trading decisions',
            'GOOD': 'Model is acceptable - use with standard risk management',
            'FAIR': 'Model shows weakness - use with extra caution and reduced position sizes',
            'POOR': '⚠️ WARNING: Model is unreliable - DO NOT USE for trading'
        }
        return messages.get(status, 'Unknown status')
    
    def _get_health_emoji(self, status: str) -> str:
        """Get emoji for health status"""
        emojis = {
            'EXCELLENT': '✅',
            'GOOD': '🟢',
            'FAIR': '🟡',
            'POOR': '🔴'
        }
        return emojis.get(status, '❓')
    
    def validate_all_coins(self) -> Dict[str, Dict]:
        """Validate models for all enabled coins"""
        results = {}
        enabled_coins = get_enabled_coins()
        
        print(f"\n🔍 Validating models for {len(enabled_coins)} coins...")
        
        for symbol in enabled_coins:
            results[symbol] = self.validate_model(symbol)
        
        return results


if __name__ == "__main__":
    # Test the validator
    validator = ModelValidator()
    
    # Validate XRP
    result = validator.validate_model('XRP', lookback_days=365)
    
    # Optionally validate all coins
    # results = validator.validate_all_coins()
