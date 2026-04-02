"""
Send bot-mockup.gif to the admin via Telegram sendAnimation API.
Usage: python scripts/send_mockup_gif.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from telegram import Bot

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_TELEGRAM_ID"])
GIF_PATH = Path(__file__).parent.parent / "landing" / "public" / "bot-mockup.gif"


async def main():
    if not GIF_PATH.exists():
        print(f"GIF not found at {GIF_PATH}")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    print(f"Sending {GIF_PATH.name} ({GIF_PATH.stat().st_size // 1024} KB) to chat {ADMIN_ID}...")

    with open(GIF_PATH, "rb") as f:
        msg = await bot.send_animation(
            chat_id=ADMIN_ID,
            animation=f,
            caption="🎬 TCG Scout bot demo",
        )

    print(f"Sent! Message ID: {msg.message_id}")


asyncio.run(main())
