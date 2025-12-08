"""
Check VPS position distribution per strategy
"""
import subprocess
import json

def check_vps_positions():
    print("\n" + "="*80)
    print("📊 VPS POSITION DISTRIBUTION ANALYSIS")
    print("="*80)
    
    # Query VPS database
    query = '''
import sqlite3
conn = sqlite3.connect(\\\"/Antigravity/antigravity/scratch/crypto_trading_bot/data/trades.db\\\")
cursor = conn.cursor()

# Get positions per strategy
cursor.execute(\\\"\\\"\\\"
SELECT 
    strategy,
    COUNT(*) as positions,
    COUNT(DISTINCT symbol) as unique_symbols,
    SUM(cost) as total_exposure
FROM positions 
WHERE status='OPEN'
GROUP BY strategy
\\\"\\\"\\\")

results = cursor.fetchall()
for r in results:
    print(f\\\"{r[0]}|{r[1]}|{r[2]}|{r[3]:.2f}\\\")

conn.close()
'''
    
    try:
        result = subprocess.run(
            ['ssh', 'root@72.60.40.29', f'python3 -c "{query}"'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            
            print(f"\n{'Strategy':<30} {'Positions':<12} {'Symbols':<10} {'Exposure':>12}")
            print("-" * 80)
            
            total_positions = 0
            total_exposure = 0
            
            for line in lines:
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) == 4:
                        strategy, positions, symbols, exposure = parts
                        positions = int(positions)
                        symbols = int(symbols)
                        exposure = float(exposure)
                        
                        total_positions += positions
                        total_exposure += exposure
                        
                        print(f"{strategy:<30} {positions:<12} {symbols:<10} ${exposure:>11,.2f}")
            
            print("-" * 80)
            print(f"{'TOTAL':<30} {total_positions:<12} {'':<10} ${total_exposure:>11,.2f}")
            print()
            
            # Configuration limits from run_bot.py
            print("📋 CONFIGURED LIMITS (from run_bot.py):")
            print("-" * 80)
            configs = [
                ("SMA Trend Bot", 5, 800),
                ("Buy-the-Dip Strategy", 20, 800),
                ("Hyper-Scalper Bot", 4, 800),
                ("Hidden Gem Monitor", 20, 100),
                ("Grid Bot BTC", 1, 1000),
                ("Grid Bot ETH", 1, 1000)
            ]
            
            print(f"{'Strategy':<30} {'Max Symbols':<12} {'Per Symbol':>12} {'Max Exposure':>14}")
            print("-" * 80)
            
            total_max_exposure = 0
            for name, symbols, per_symbol in configs:
                max_exp = symbols * per_symbol
                total_max_exposure += max_exp
                print(f"{name:<30} {symbols:<12} ${per_symbol:>11} ${max_exp:>13,.0f}")
            
            print("-" * 80)
            print(f"{'TOTAL ALLOWED':<30} {'51':<12} {'':<12} ${total_max_exposure:>13,.0f}")
            
            # Analysis
            print("\n✅ VERDICT:")
            if total_positions <= 51:
                utilization = (total_positions / 51) * 100
                print(f"   Current positions ({total_positions}) are WITHIN configured limits (max 51)")
                print(f"   Capacity utilization: {utilization:.1f}%")
                print(f"   Available slots: {51 - total_positions}")
            else:
                print(f"   ⚠️  OVER LIMIT: {total_positions} positions > 51 max configured!")
            
        else:
            print(f"❌ SSH command failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ SSH connection timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    check_vps_positions()
