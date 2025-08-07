import psycopg2
import os

# Get DB connection from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect and return cursor + connection
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn, conn.cursor()

# Create tables
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
            fresh_wallet BOOLEAN DEFAULT FALSE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watched_tokens (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            token_symbol TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

# Add user
def add_user(user_id: int):
    conn, cur = get_connection()
    cur.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING;", (user_id,))
    conn.commit()
    conn.close()

# Add wallet
def add_wallet(user_id: int, address: str):
    conn, cur = get_connection()
    cur.execute("""
        INSERT INTO wallets (user_id, address)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING;
    """, (user_id, address))
    conn.commit()
    conn.close()

# Remove wallet
def remove_wallet(user_id: int, address: str):
    conn, cur = get_connection()
    cur.execute("""
        DELETE FROM wallets
        WHERE user_id = %s AND address = %s;
    """, (user_id, address))
    conn.commit()
    conn.close()

# Get all wallets for user
def get_user_wallets(user_id: int):
    conn, cur = get_connection()
    cur.execute("""
        SELECT id, address, name, min_sol, max_sol, fresh_wallet
        FROM wallets
        WHERE user_id = %s;
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

# Update wallet name
def update_wallet_name(wallet_id: int, new_name: str):
    conn, cur = get_connection()
    cur.execute("""
        UPDATE wallets
        SET name = %s
        WHERE id = %s;
    """, (new_name, wallet_id))
    conn.commit()
    conn.close()

# Update min/max SOL thresholds
def update_wallet_thresholds(wallet_id: int, min_sol: float, max_sol: float):
    conn, cur = get_connection()
    cur.execute("""
        UPDATE wallets
        SET min_sol = %s,
            max_sol = %s
        WHERE id = %s;
    """, (min_sol, max_sol, wallet_id))
    conn.commit()
    conn.close()

# Toggle fresh wallet flag
def toggle_fresh_wallet_flag(wallet_id: int):
    conn, cur = get_connection()
    cur.execute("""
        UPDATE wallets
        SET fresh_wallet = NOT fresh_wallet
        WHERE id = %s;
    """, (wallet_id,))
    conn.commit()
    conn.close()
