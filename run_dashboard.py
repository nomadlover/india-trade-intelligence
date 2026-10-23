"""Launcher script for India Trade Intelligence Streamlit Dashboard."""
import subprocess
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent
    app_path = root / "india_trade_intelligence" / "app.py"
    
    print("=" * 60)
    print("STARTING INDIA TRADE INTELLIGENCE DASHBOARD")
    print("=" * 60)
    print(f"Target App: {app_path}")
    print("Launching Streamlit...")
    
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.headless", "true",
        "--server.port", "8501"
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
