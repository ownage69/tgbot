import sqlite3

# Доступные лабы
AVAILABLE_LABS = ['1']

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
    cur.execute('''
        CREATE TABLE IF NOT EXISTS queue (
            user_id INTEGER,
            fi TEXT,
            subgroup TEXT,
            lab_number TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_to_queue(user_id, fi, subgroup, lab_number):
    if lab_number not in AVAILABLE_LABS:
        return "not_available"

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM queue WHERE user_id = ? AND lab_number = ?", (user_id, lab_number))
    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute("INSERT INTO queue (user_id, fi, subgroup, lab_number) VALUES (?, ?, ?, ?)",
                   (user_id, fi, subgroup, lab_number))

    conn.commit()
    conn.close()
    return True

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

def get_lab_queue_by_subgroup(subgroup):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT lab_number, fi
        FROM queue
        WHERE subgroup = ?
        ORDER BY lab_number ASC, timestamp ASC
    ''', (subgroup,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_labs(user_id):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT lab_number FROM queue WHERE user_id = ?", (user_id,))
    labs = [row[0] for row in cur.fetchall()]
    conn.close()
    return labs

def is_fi_taken(fi):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE fi = ?", (fi,))
    result = cur.fetchone()
    conn.close()
    return result is not None

def remove_user_from_lab(user_id, lab_number):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM queue WHERE user_id = ? AND lab_number = ?", (user_id, lab_number))
    conn.commit()
    changes = cursor.rowcount
    conn.close()
    return changes > 0
