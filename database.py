import sqlite3

def init_db():
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            fi TEXT NOT NULL,
            subgroup TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, fi):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO users (user_id, fi) VALUES (?, ?)", (user_id, fi))
    conn.commit()
    conn.close()

def update_subgroup(user_id, subgroup):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("UPDATE users SET subgroup = ? WHERE user_id = ?", (subgroup, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT fi, subgroup FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result
