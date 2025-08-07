import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")  # From Railway Postgres

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def create_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            address TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
