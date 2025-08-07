import os
from dotenv import load_dotenv
from database import create_tables

# Load environment variables from .env file
load_dotenv()

# Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL")

# Helius API key
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
