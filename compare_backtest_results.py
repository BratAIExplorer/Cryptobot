#!/usr/bin/env python3
"""
Compare Backtest Results: Binance vs MEXC
Generates comparison report showing which strategies work better on which exchange

DATA SOURCES:
- Binance: Production data from VPS (backups_binance/)
- MEXC: Backtest results (backtest_results/mexc/)
"""
import json
import pandas as pd
import os
from datetime import datetime

class BacktestComparator:
    """Compare strategy performance across Binance and MEXC"""
    
    def __init__(self):
        self.binance_results = None
        self.mexc_results = {}
        
    def load_binance_results(self, audit_file='backups_binance/binance_final_audit_*.json'):
        """Load Binance production results"""
        import glob
        files = glob.glob(audit_file)
        
        if not files:
            print(f"⚠️  No Binance audit files found: {audit_file}")
            return False
        
        with open(files[0], 'r') as f:
            self.binance_results = json.load(f)
        
        print(f"✅ Loaded Binance results: {files[0]}")
        return True
    
    def load_mexc_results(self, results_dir='backtest_results'):
        """Load all MEXC backtest results"""
        if not os.path.exists(results_dir):
            print(f"⚠️  MEXC results directory not found: {results_dir}")
            return False
        
        json_files = [f for f in os.listdir(results_dir) if f.endswith('_report.json')]
        
        for file in json_files:
            filepath = os.path.join(results_dir, file)
            with open(filepath, 'r') as f:
                data = json.load(f)
                strategy = data.get('strategy', 'unknown')
                self.mexc_results[strategy] = data
        
        print(f"✅ Loaded {len(self.mexc_results)} MEXC backtest results")
        return True
    
    def generate_comparison(self):
        """Generate comparison report"""
        if not self.binance_results or not self.mexc_results:
            print("❌ Missing data - load both Binance and MEXC results first")
            return None
        
        print(f"\n{'='*80}")
        print(f"BINANCE vs MEXC BACKTEST COMPARISON")
        print(f"{'='*80}\n")
        
        # Extract Binance strategy breakdown
        binance_strategies = self.binance_results.get('strategy_breakdown', [])
        
        comparison = []
        
        for binance_strat in binance_strategies:
            strat_name = binance_strat['strategy']
            
            # Find matching MEXC result
            mexc_strat = None
            for mexc_key, mexc_data in self.mexc_results.items():
                if strat_name.lower().replace(' ', '_') in mexc_key.lower():
                    mexc_strat = mexc_data
                    break
            
            row = {
                'Strategy': strat_name,
                'Binance_Trades': binance_strat.get('trades', 0),
                'Binance_WinRate': binance_strat.get('win_rate', 0),
                'Binance_ROI': (binance_strat.get('total_pnl', 0) / 800) * 100 if binance_strat.get('trades') else 0,
                'MEXC_Trades': mexc_strat.get('total_trades', 0) if mexc_strat else 0,
                'MEXC_WinRate': mexc_strat.get('win_rate_pct', 0) if mexc_strat else 0,
                'MEXC_ROI': mexc_strat.get('roi_pct', 0) if mexc_strat else 0,
            }
            
            # Calculate deltas
            row['WinRate_Delta'] = row['MEXC_WinRate'] - row['Binance_WinRate']
            row['ROI_Delta'] = row['MEXC_ROI'] - row['Binance_ROI']
            
            # Verdict
            if row['MEXC_WinRate'] > 55 and row['MEXC_ROI'] > 15:
                row['Verdict'] = '✅ DEPLOY'
            elif row['MEXC_WinRate'] > 50 and row['MEXC_ROI'] > 10:
                row['Verdict'] = '🟡 OPTIMIZE'
            else:
                row['Verdict'] = '🔴 REJECT'
            
            comparison.append(row)
        
        df = pd.DataFrame(comparison)
        
        # Print table
        print(df.to_string(index=False))
        
        # Summary
        deployable = len(df[df['Verdict'] == '✅ DEPLOY'])
        needs_work = len(df[df['Verdict'] == '🟡 OPTIMIZE'])
        rejected = len(df[df['Verdict'] == '🔴 REJECT'])
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Ready to Deploy: {deployable}/5 strategies")
        print(f"🟡 Needs Optimization: {needs_work}/5 strategies")
        print(f"🔴 Reject: {rejected}/5 strategies")
        print(f"{'='*80}\n")
        
        # Save to HTML
        output_file = f'backtest_results/comparison_binance_vs_mexc_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        
        html = f"""
        <html>
        <head>
            <title>Binance vs MEXC Comparison</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .deploy {{ background-color: #d4edda; }}
                .optimize {{ background-color: #fff3cd; }}
                .reject {{ background-color: #f8d7da; }}
            </style>
        </head>
        <body>
            <h1>Binance vs MEXC Strategy Comparison</h1>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            {df.to_html(index=False, classes='comparison')}
            <h2>Summary</h2>
            <ul>
                <li>✅ Ready to Deploy: {deployable}/5</li>
                <li>🟡 Needs Optimization: {needs_work}/5</li>
                <li>🔴 Reject: {rejected}/5</li>
            </ul>
        </body>
        </html>
        """
        
        os.makedirs('backtest_results', exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"✅ Comparison report saved: {output_file}")
        
        return df

if __name__ == "__main__":
    comparator = BacktestComparator()
    
    # Load results
    comparator.load_binance_results()
    comparator.load_mexc_results()
    
    # Generate comparison
    comparator.generate_comparison()
