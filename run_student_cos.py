"""
Convenient entry point and CLI launcher for Student Chief of Staff.
Usage:
    python run_student_cos.py            # Launch the Streamlit Personal OS
    python run_student_cos.py --test     # Run automated pytest suite
    python run_student_cos.py --telegram # Run optional Telegram bot
"""
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
APP_PATH = ROOT_DIR / "student_cos" / "app.py"


def main():
    if "--test" in sys.argv:
        print("[Chief of Staff] Running automated pytest suite...")
        res = subprocess.run([sys.executable, "-m", "pytest", "tests", "-v"], cwd=ROOT_DIR)
        sys.exit(res.returncode)

    if "--telegram" in sys.argv:
        print("[Chief of Staff] Launching optional Telegram bot gateway...")
        res = subprocess.run([sys.executable, "-m", "student_cos.telegram_bot"], cwd=ROOT_DIR)
        sys.exit(res.returncode)

    print(f"[Chief of Staff] Starting Student Chief of Staff at http://localhost:8501 ...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(APP_PATH),
        "--server.headless=true",
        "--server.port=8501"
    ], cwd=ROOT_DIR)


if __name__ == "__main__":
    main()
