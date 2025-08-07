from config import get_db_connection

def add_user(telegram_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (telegram_id) VALUES (%s) ON CONFLICT DO NOTHING;", (telegram_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_user_wallets(telegram_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT wallet_address FROM wallets WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s);", (telegram_id,))
    wallets = cur.fetchall()
    cur.close()
    conn.close()
    return wallets
