import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import Database, CircuitBreaker

def force_resume():
    print("🚀 Starting Emergency Bot Resumption...")
    
    # Initialize DB (default targets trades_v3.db)
    db = Database()
    session = db.get_session()
    
    try:
        # 1. Reset Circuit Breaker
        cb = session.query(CircuitBreaker).filter_by(id=1).first()
        if cb:
            print(f"  -> Found Circuit Breaker: errors={cb.consecutive_errors}, open={cb.is_open}")
            cb.is_open = False
            cb.consecutive_errors = 0
            cb.last_reset_time = datetime.utcnow()
            print("  ✅ Circuit Breaker RESET successfully.")
        else:
            # Create if missing (unlikely but safe)
            new_cb = CircuitBreaker(id=1, is_open=False, consecutive_errors=0, last_reset_time=datetime.utcnow())
            session.add(new_cb)
            print("  ⚠️ Circuit Breaker row missing. Created new record.")
        
        session.commit()
        print("\n🎉 Bot is now ready to resume trading.")
        print("Run 'pm2 restart crypto_bot' to apply changes.")
        
    except Exception as e:
        session.rollback()
        print(f"❌ ERROR: Failed to reset circuit breaker: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    force_resume()
