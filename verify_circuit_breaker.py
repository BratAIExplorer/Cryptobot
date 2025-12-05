from logger import TradeLogger
import time

def verify_circuit_breaker():
    logger = TradeLogger()
    
    print("1. Initial Status:")
    status = logger.get_circuit_breaker_status()
    print(status)
    
    print("\n2. Simulating 10 Errors...")
    for i in range(10):
        count = logger.increment_circuit_breaker_errors()
        print(f"Error #{count}")
        
    print("\n3. Status after errors:")
    status = logger.get_circuit_breaker_status()
    print(status)
    
    if status['is_open']:
        print("✅ Circuit Breaker OPENED correctly.")
    else:
        print("❌ Circuit Breaker FAILED to open.")
        
    print("\n4. Resetting...")
    logger.reset_circuit_breaker()
    status = logger.get_circuit_breaker_status()
    print(status)
    
    if not status['is_open'] and status['consecutive_errors'] == 0:
        print("✅ Circuit Breaker RESET correctly.")
    else:
        print("❌ Circuit Breaker FAILED to reset.")

if __name__ == "__main__":
    verify_circuit_breaker()
