import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("Crypto Trading Bot - Core Engine Initialized")
    print("Please run the dashboard using: streamlit run dashboard/app.py")

if __name__ == "__main__":
    main()
