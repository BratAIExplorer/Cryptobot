import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Patch UnifiedExchange before anything else
with patch('core.engine.UnifiedExchange') as MockExchange, \
     patch('core.engine.TelegramNotifier') as MockNotifier, \
     patch('core.engine.VetoManager') as MockVeto, \
     patch('core.engine.SystemMonitor') as MockMonitor:
    
    from core.engine import TradingEngine
    from core.logger import TradeLogger

    def verify():
        print("--- Verifying Dashboard Data Logic ---")
        
        # Initialize engine in paper mode with test database
        db_path = 'data/test_verify.db'
        if os.path.exists(db_path):
            os.remove(db_path)
            
        print("Initializing Engine...")
        engine = TradingEngine(mode='paper', db_path=db_path)
        
        # Add a mock bot with a specific budget
        test_budget = 4000
        print(f"Adding bot with budget ${test_budget}...")
        engine.add_bot({
            'name': 'Test SMA Bot',
            'type': 'SMA',
            'symbols': ['BTC/USDT'],
            'amount': 800,
            'initial_balance': test_budget
        })
        
        # Manually log a trade to simulate history
        print("Logging mock trade...")
        engine.logger.log_trade(
            strategy='Test SMA Bot',
            symbol='BTC/USDT',
            side='BUY',
            price=10000,
            amount=0.08,
            exchange='MEXC'
        )
        
        # Simulate bot startup logic
        print("\nSimulating bot startup updates...")
        all_trades = engine.logger.get_trades()
        for bot in engine.active_bots:
            # Get actual trade count for this bot
            if not all_trades.empty:
                bot_trades = all_trades[all_trades['strategy'] == bot['name']]
                total_trades = len(bot_trades)
            else:
                total_trades = 0
                
            total_pnl = engine.logger.get_pnl_summary(bot['name'])
            initial_bal = bot.get('initial_balance', 50000.0)
            wallet_balance = engine.logger.get_wallet_balance(bot['name'], initial_balance=initial_bal)
            
            print(f"Bot: {bot['name']}")
            print(f" - Trades: {total_trades} (Expected: 1)")
            print(f" - Balance: ${wallet_balance} (Expected: 4000.0)")
            
            # Verify status in DB
            engine.logger.update_bot_status(bot['name'], 'RUNNING', total_trades, total_pnl, wallet_balance)
            status_df = engine.logger.get_bot_status(bot['name'])
            db_trades = status_df.iloc[0]['total_trades']
            db_balance = status_df.iloc[0]['wallet_balance']
            
            print(f" - DB Trades: {db_trades}")
            print(f" - DB Balance: ${db_balance}")
            
            assert db_trades == 1, f"Trade count mismatch: {db_trades}"
            assert db_balance == float(test_budget), f"Balance mismatch: {db_balance}"
            
        print("\n✅ Verification SUCCESS: Trade counts and budgets are correctly handled.")
        
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)

    if __name__ == "__main__":
        try:
            verify()
        except Exception as e:
            print(f"❌ Verification FAILED: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
