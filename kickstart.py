"""
CryptoBots V3 - Main Launcher
Launch the web dashboard or run bot in headless mode.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Main launcher function."""
    print("=" * 60)
    print("🤖 CryptoBots V3 - Intelligent Crypto Trading Bot")
    print("=" * 60)
    print()
    print("Select launch mode:")
    print("1. 🌐 Web Dashboard (Recommended)")
    print("2. 💻 Command Line Mode")
    print("3. 🏥 Health Monitor Only")
    print("4. ❌ Exit")
    print()
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == "1":
        launch_dashboard()
    elif choice == "2":
        launch_cli()
    elif choice == "3":
        launch_health_monitor()
    elif choice == "4":
        print("👋 Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid choice. Please try again.")
        main()


def launch_dashboard():
    """Launch the Streamlit web dashboard."""
    print("\n🚀 Launching Web Dashboard...")
    print("📍 Access the dashboard at: http://localhost:8501")
    print("Press Ctrl+C to stop\n")
    
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "dashboard.py",
        "--server.port=8501",
        "--server.address=localhost",
        "--theme.primaryColor=#667eea",
        "--theme.backgroundColor=#0e1117",
        "--theme.secondaryBackgroundColor=#262730",
        "--theme.textColor=#fafafa"
    ])


def launch_cli():
    """Launch command-line trading bot."""
    print("\n💻 Command Line Mode")
    print("This feature is coming soon!")
    print("For now, please use the Web Dashboard.\n")
    input("Press Enter to return to menu...")
    main()


def launch_health_monitor():
    """Launch health monitor in standalone mode."""
    print("\n🏥 Launching Health Monitor...")
    print("Press Ctrl+C to stop\n")
    
    subprocess.run([
        sys.executable,
        "health_monitor.py",
        "--debug",
        "--interval=60"
    ])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 CryptoBots V3 stopped by user")
        sys.exit(0)
