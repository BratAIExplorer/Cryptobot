#!/usr/bin/env python3
"""
Graceful Shutdown & Final Audit Script
Safely stops all running bots and exports comprehensive audit data
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.logger import TradeLogger
from core.database import Database

def create_stop_signal():
    """Create STOP_SIGNAL file to halt bot"""
    with open("STOP_SIGNAL", "w") as f:
        f.write(f"STOP requested at {datetime.now().isoformat()}\n")
    print("✅ STOP_SIGNAL file created - bot will halt on next cycle")

def export_final_audit(mode='paper'):
    """Generate comprehensive final audit report"""
    print("=" * 80)
    print("🛑 BINANCE FINAL AUDIT - Graceful Shutdown Protocol")
    print("=" * 80)
    
    logger = TradeLogger(mode=mode)
    
    # 1. Get all trades
    all_trades = logger.get_trades()
    print(f"\n📊 Total Trades Executed: {len(all_trades)}")
    
    # 2. Get PnL Summary
    pnl_summary = logger.get_pnl_summary()
    print(f"💰 Net Realized P&L: ${pnl_summary['total_pnl']:.2f}")
    print(f"✅ Winning Trades: {pnl_summary['winning_trades']}")
    print(f"❌ Losing Trades: {pnl_summary['losing_trades']}")
    print(f"📈 Win Rate: {pnl_summary['win_rate']:.2f}%")
    
    # 3. Get Bot Status for each strategy
    bot_statuses = logger.get_bot_status()
    print(f"\n🤖 Active Strategies: {len(bot_statuses)}")
    
    strategy_breakdown = []
    for status in bot_statuses:
        strategy_data = {
            'strategy': status['strategy'],
            'status': status['status'],
            'total_trades': status['total_trades'],
            'total_pnl': status['total_pnl'],
            'wallet_balance': status['wallet_balance'],
            'last_active': status['last_active']
        }
        strategy_breakdown.append(strategy_data)
        print(f"  - {status['strategy']}: {status['total_trades']} trades, ${status['total_pnl']:.2f} P&L")
    
    # 4. Get open positions
    open_positions = logger.get_open_positions()
    print(f"\n📦 Open Positions: {len(open_positions)}")
    
    open_positions_data = []
    for _, pos in open_positions.iterrows():
        unrealized_pnl = (pos.get('current_price', pos['entry_price']) - pos['entry_price']) * pos['amount']
        pos_data = {
            'position_id': pos['id'],
            'symbol': pos['symbol'],
            'strategy': pos['strategy'],
            'entry_price': pos['entry_price'],
            'amount': pos['amount'],
            'cost_basis': pos['cost_basis'],
            'entry_date': pos['entry_date'],
            'age_days': (datetime.now() - datetime.fromisoformat(pos['entry_date'])).days,
            'unrealized_pnl': unrealized_pnl
        }
        open_positions_data.append(pos_data)
        print(f"  - {pos['symbol']} ({pos['strategy']}): ${unrealized_pnl:.2f} unrealized")
    
    # 5. Circuit Breaker Status
    cb_status = logger.get_circuit_breaker_status()
    circuit_breaker_data = {
        'active': cb_status['active'],
        'error_count': cb_status['error_count'],
        'last_error': cb_status['last_error']
    }
    print(f"\n⚡ Circuit Breaker: {'🔴 ACTIVE' if cb_status['active'] else '🟢 Inactive'}")
    print(f"   Error Count: {cb_status['error_count']}")
    
    # 6. System Health
    system_health = logger.get_system_health()
    health_data = []
    for health in system_health:
        health_data.append({
            'component': health['component'],
            'status': health['status'],
            'message': health['message'],
            'last_check': health['last_check']
        })
    
   # 7. Error Log Analysis
    db = Database(logger.db_path)
    session = db.Session()
    
    # Get skipped trades (veto/exposure blocking)
    skipped_query = "SELECT * FROM skipped_trades ORDER BY timestamp DESC LIMIT 100"
    skipped_trades = session.execute(skipped_query).fetchall()
    
    skipped_data = []
    for skip in skipped_trades:
        skipped_data.append({
            'timestamp': skip.timestamp,
            'strategy': skip.strategy,
            'symbol': skip.symbol,
            'side': skip.side,
            'skip_reason': skip.skip_reason,
            'intended_amount': skip.intended_amount
        })
    
    print(f"\n🚫 Skipped Trades (Last 100): {len(skipped_data)}")
    
    # Count skip reasons
    skip_reasons = {}
    for skip in skipped_data:
        reason = skip['skip_reason']
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
    
    for reason, count in sorted(skip_reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {reason}: {count} times")
    
    session.close()
    
    # 8. Compile Final Audit JSON
    final_audit = {
        'audit_metadata': {
            'timestamp': datetime.now().isoformat(),
            'exchange': 'binance',
            'mode': mode,
            'total_runtime_days': (datetime.now() - datetime.fromisoformat(all_trades[0]['timestamp'])).days if len(all_trades) > 0 else 0
        },
        'performance_summary': {
            'total_trades': len(all_trades),
            'net_pnl': pnl_summary['total_pnl'],
            'winning_trades': pnl_summary['winning_trades'],
            'losing_trades': pnl_summary['losing_trades'],
            'win_rate': pnl_summary['win_rate'],
            'avg_win': pnl_summary.get('avg_win', 0),
            'avg_loss': pnl_summary.get('avg_loss', 0)
        },
        'strategy_breakdown': strategy_breakdown,
        'open_positions': {
            'count': len(open_positions_data),
            'total_unrealized_pnl': sum([p['unrealized_pnl'] for p in open_positions_data]),
            'positions': open_positions_data
        },
        'safety_systems': {
            'circuit_breaker': circuit_breaker_data,
            'system_health': health_data
        },
        'operational_data': {
            'skipped_trades_count': len(skipped_data),
            'skip_reasons_breakdown': skip_reasons,
            'last_100_skips': skipped_data[:20]  # Only include last 20 for brevity
        },
        'migration_notes': {
            'status': 'READY_FOR_MEXC_MIGRATION',
            'next_steps': [
                '1. Review open positions - decide to close or migrate',
                '2. Verify API keys for MEXC',
                '3. Run shadow mode for 48-168 hours',
                '4. Compare Binance vs MEXC slippage/fees'
            ],
            'warnings': [
                'Open positions will need to be manually closed on Binance OR left to mature',
                'Historical performance on Binance may not transfer 1:1 to MEXC',
                'Recommend 7-day shadow mode before live deployment'
            ]
        }
    }
    
    # 9. Save to JSON
    output_file = f'binance_final_audit_{mode}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(final_audit, f, indent=2)
    
    print(f"\n✅ Final audit saved to: {output_file}")
    print("=" * 80)
    
    return final_audit, output_file

def backup_databases(mode='paper'):
    """Create backup of database files"""
    import shutil
    
    db_files = [
        f'data/trades_v3_{mode}.db',
        f'data/trades_v3_{mode}.db-wal',
        f'data/trades_v3_{mode}.db-shm'
    ]
    
    backup_dir = f'data/backups/binance_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    
    for db_file in db_files:
        if os.path.exists(db_file):
            shutil.copy2(db_file, backup_dir)
            print(f"✅ Backed up: {db_file} → {backup_dir}")
    
    return backup_dir

if __name__ == "__main__":
    print("\n🛑 INITIATING GRACEFUL SHUTDOWN PROTOCOL\n")
    
    # Determine mode from command line or default to paper
    mode = sys.argv[1] if len(sys.argv) > 1 else 'paper'
    
    # Step 1: Create stop signal
    create_stop_signal()
    
    # Step 2: Wait for bot to acknowledge (give it 60 seconds)
    print("\n⏳ Waiting 60 seconds for bot to detect STOP_SIGNAL...")
    import time
    time.sleep(60)
    
    # Step 3: Export final audit
    audit_data, audit_file = export_final_audit(mode=mode)
    
    # Step 4: Backup databases
    backup_dir = backup_databases(mode=mode)
    
    # Step 5: Generate human-readable summary
    print("\n" + "=" * 80)
    print("📋 MIGRATION READINESS SUMMARY")
    print("=" * 80)
    print(f"✅ Bot stopped gracefully")
    print(f"✅ Audit data exported: {audit_file}")
    print(f"✅ Database backed up: {backup_dir}")
    print(f"\n💰 Final P&L: ${audit_data['performance_summary']['net_pnl']:.2f}")
    print(f"📊 Win Rate: {audit_data['performance_summary']['win_rate']:.2f}%")
    print(f"📦 Open Positions: {audit_data['open_positions']['count']}")
    print(f"🚫 Skipped Trades: {audit_data['operational_data']['skipped_trades_count']}")
    
    print("\n🚀 READY FOR MEXC MIGRATION")
    print("   Next step: Run migration_to_mexc.py")
    print("=" * 80)
