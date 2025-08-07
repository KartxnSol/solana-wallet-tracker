import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn, conn.cursor()

def create_tables():
    conn, cur = get_connection()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS wallets (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id),
        address TEXT NOT NULL,
        name TEXT DEFAULT '',
        min_sol FLOAT DEFAULT 0,
        max_sol FLOAT DEFAULT 1000000,
        fresh_wallet BOOLEAN DEFAULT TRUE
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notified (
        wallet_id INTEGER,
        tx_signature TEXT,
        PRIMARY KEY (wallet_id, tx_signature)
    );
    """)
    conn.commit()
    conn.close()

def add_user(user_id: int):
    conn, cur = get_connection()
    cur.execute(
        "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING;", 
        (user_id,)
    )
    conn.commit()
    conn.close()

def add_wallet(user_id: int, address: str):
    conn, cur = get_connection()
    cur.execute(
        "INSERT INTO wallets (user_id, address) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
        (user_id, address)
    )
    conn.commit()
    conn.close()

def remove_wallet(user_id: int, address: str):
    conn, cur = get_connection()
    cur.execute(
        "DELETE FROM wallets WHERE user_id = %s AND address = %s;",
        (user_id, address)
    )
    conn.commit()
    conn.close()

def get_user_wallets(user_id: int):
    conn, cur = get_connection()
    cur.execute(
        "SELECT id, address, name, min_sol, max_sol, fresh_wallet FROM wallets WHERE user_id = %s;",
        (user_id,)
    )
    wallets = cur.fetchall()
    conn.close()
    return wallets

def get_wallet_by_address(address: str):
    conn, cur = get_connection()
    cur.execute(
        "SELECT id, user_id, address, name, min_sol, max_sol, fresh_wallet FROM wallets WHERE address = %s;",
        (address,)
    )
    result = cur.fetchone()
    conn.close()
    return result

def update_wallet_name(wallet_id: int, name: str):
    conn, cur = get_connection()
    cur.execute("UPDATE wallets SET name = %s WHERE id = %s;", (name, wallet_id))
    conn.commit()
    conn.close()

def update_wallet_thresholds(wallet_id: int, min_sol: float, max_sol: float):
    conn, cur = get_connection()
    cur.execute(
        "UPDATE wallets SET min_sol = %s, max_sol = %s WHERE id = %s;",
        (min_sol, max_sol, wallet_id)
    )
    conn.commit()
    conn.close()

def toggle_fresh_wallet_flag(wallet_id: int):
    conn, cur = get_connection()
    cur.execute(
        "UPDATE wallets SET fresh_wallet = NOT fresh_wallet WHERE id = %s;",
        (wallet_id,)
    )
    conn.commit()
    conn.close()

def is_tx_notified(wallet_id: int, signature: str) -> bool:
    conn, cur = get_connection()
    cur.execute(
        "SELECT 1 FROM notified WHERE wallet_id = %s AND tx_signature = %s;",
        (wallet_id, signature)
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def log_notified_tx(wallet_id: int, signature: str):
    conn, cur = get_connection()
    cur.execute(
        "INSERT INTO notified (wallet_id, tx_signature) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
        (wallet_id, signature)
    )
    conn.commit()
    conn.close()
