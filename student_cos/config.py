"""
Configuration settings for Student Chief of Staff.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DEFAULT_DB_PATH = os.environ.get("STUDENT_COS_DB", str(ROOT_DIR / "student_cos.db"))

# Default work day constraints
DEFAULT_WORK_START = "09:00"
DEFAULT_WORK_END = "18:00"
DEFAULT_BREAK_MINUTES = 15
DEFAULT_DEEP_WORK_BLOCK_MINUTES = 90

# AI Provider Settings
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALLOWED_USERS = [
    int(u.strip()) for u in os.environ.get("TELEGRAM_ALLOWED_USERS", "").split(",") if u.strip().isdigit()
]
