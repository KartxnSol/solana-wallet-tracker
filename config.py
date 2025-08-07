import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS wallets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            wallet_address TEXT NOT NULL,
            display_name TEXT,
            sol_min_threshold NUMERIC,
            sol_max_threshold NUMERIC,
            fresh_wallet_only BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS watched_tokens (
            id SERIAL PRIMARY KEY,
            wallet_id INTEGER REFERENCES wallets(id),
            token_mint_address TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
