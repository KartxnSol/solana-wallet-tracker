from config import get_connection

def add_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_user_wallets(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT address FROM wallets WHERE user_id = %s;", (user_id,))
    wallets = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return wallets
