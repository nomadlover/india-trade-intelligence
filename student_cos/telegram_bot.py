"""
Optional Telegram Bot Interface for Student Chief of Staff.
Allows students to interact with their personal operating system on the go.
Runs independently without blocking the local Streamlit application.
"""
from __future__ import annotations

import os
import sys
import time
import requests
from typing import Optional, Dict, Any

from student_cos.config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USERS
from student_cos.db import Database
from student_cos.tools import ChiefOfStaffTools
from student_cos.ai.assistant import StudentChiefOfStaff


class StudentTelegramBot:
    """
    Lightweight Telegram bot using direct Telegram Bot API polling.
    Zero external bot framework dependencies required.
    """

    def __init__(self, token: Optional[str] = None, db: Optional[Database] = None):
        self.token = token or TELEGRAM_BOT_TOKEN or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.db = db or Database()
        self.tools = ChiefOfStaffTools(self.db)
        self.assistant = StudentChiefOfStaff(self.db)
        self.offset = 0

    def is_configured(self) -> bool:
        return bool(self.token and self.token.strip())

    def send_message(self, chat_id: int, text: str) -> bool:
        try:
            resp = requests.post(
                f"{self.api_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"[TelegramBot] Send error: {e}")
            return False

    def handle_update(self, update: Dict[str, Any]) -> None:
        message = update.get("message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        from_user = message.get("from", {}).get("id")

        # Security check: if whitelist is specified, verify sender
        if TELEGRAM_ALLOWED_USERS and from_user not in TELEGRAM_ALLOWED_USERS:
            self.send_message(chat_id, "⛔ Access denied: unauthorized user ID.")
            return

        text = message.get("text", "").strip()
        if not text:
            return

        print(f"[TelegramBot] Received message from {chat_id}: {text}")

        # Command handling
        if text.startswith("/start") or text.startswith("/help"):
            reply = (
                "🎓 *Student Chief of Staff Telegram Gateway*\n\n"
                "Available commands:\n"
                "• *What's my priority today?* or `/priority`\n"
                "• *Plan my day* or `/plan`\n"
                "• *What deadlines are coming up?* or `/deadlines`\n"
                "• *Summarize my project progress* or `/summary`\n"
                "• `/add <task title>` (e.g. `/add Study for midterms`)\n"
                "• Or just send any natural language question!"
            )
            self.send_message(chat_id, reply)
            return

        if text.startswith("/add "):
            task_title = text[5:].strip()
            res = self.tools.create_task(title=task_title)
            if res.success:
                self.send_message(chat_id, f"✅ Created task: *{task_title}* (ID: {res.data['id']})")
            else:
                self.send_message(chat_id, f"⚠️ Error: {res.error}")
            return

        # Route through assistant
        response = self.assistant.process_message(text)
        self.send_message(chat_id, response.text)

    def run_polling(self) -> None:
        if not self.is_configured():
            print("[TelegramBot] Error: TELEGRAM_BOT_TOKEN not provided.")
            print("To enable Telegram integration:")
            print("  1. Create a bot via @BotFather on Telegram")
            print("  2. Set TELEGRAM_BOT_TOKEN=your_token in environment or config.py")
            print("  3. Run: python -m student_cos.telegram_bot")
            return

        print("[TelegramBot] Starting long polling... Press Ctrl+C to stop.")
        while True:
            try:
                resp = requests.get(
                    f"{self.api_url}/getUpdates",
                    params={"offset": self.offset, "timeout": 25},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        self.offset = update["update_id"] + 1
                        self.handle_update(update)
                else:
                    time.sleep(2)
            except KeyboardInterrupt:
                print("\n[TelegramBot] Stopping bot gracefully.")
                break
            except Exception as e:
                print(f"[TelegramBot] Polling loop error: {e}")
                time.sleep(3)


if __name__ == "__main__":
    bot = StudentTelegramBot()
    bot.run_polling()
