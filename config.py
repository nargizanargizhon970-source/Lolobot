import os
import sys
from dotenv import load_dotenv

# Windows консолида UTF-8 белгилари хатосиз чиқиши учун
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

# Telegram Bot Token (@BotFather орқали олинади)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Google Gemini API калити
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    print("[DIQQAT] .env faylida BOT_TOKEN ko'rsatilmagan! Iltimos, token kiriting.")
