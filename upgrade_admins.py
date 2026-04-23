import sqlite3

conn = sqlite3.connect('maize_connect.db')

# 1. Nuke the old, simple admin table
conn.execute('DROP TABLE IF EXISTS admins')

# 2. Build the enterprise admin table
conn.execute('''
    CREATE TABLE admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        province TEXT NOT NULL,
        security_question TEXT NOT NULL,
        security_answer_hash TEXT NOT NULL
    )
''')

print("SUCCESS: Advanced multi-province admin vault created.")
conn.commit()
conn.close()