import requests
import time
import socket

def check_connectivity():
    print("🔍 DIAGNOSTIC: Connectivity Check")
    print("=" * 40)

    # 1. DNS Resolution
    try:
        ip = socket.gethostbyname("api.binance.com")
        print(f"✅ DNS Resolution (api.binance.com): {ip}")
    except Exception as e:
        print(f"❌ DNS Resolution Failed: {e}")

    # 2. Basic Internet Check
    try:
        response = requests.get("https://1.1.1.1", timeout=5)
        if response.status_code == 200:
            print("✅ Internet Access: OK")
        else:
            print(f"⚠️ Internet Access: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Internet Access Failed: {e}")

    # 3. Binance API Ping
    try:
        start = time.time()
        response = requests.get("https://api.binance.com/api/v3/ping", timeout=5)
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            print(f"✅ Binance API: Reachable ({latency:.0f}ms)")
        elif response.status_code == 403:
            print("❌ Binance API: 403 Forbidden (Possible IP Ban/Geoblock)")
        elif response.status_code == 451:
            print("❌ Binance API: 451 Unavailable (Legal Restriction)")
        else:
            print(f"❌ Binance API: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Binance API Connection Error: {e}")

if __name__ == "__main__":
    check_connectivity()
