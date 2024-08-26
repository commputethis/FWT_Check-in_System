import sqlite3

def init_db():
    conn = sqlite3.connect('attendees.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        first_name TEXT,
                        last_name TEXT,
                        preferred_name TEXT,
                        company TEXT,
                        title TEXT,
                        email TEXT,
                        checked_in BOOLEAN DEFAULT FALSE)''')
    conn.commit()
    conn.close()

init_db()