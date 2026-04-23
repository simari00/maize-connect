import sqlite3

conn = sqlite3.connect('maize_connect.db')

conn.execute('DROP TABLE IF EXISTS users')
conn.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        pin TEXT NOT NULL,
        province TEXT NOT NULL,
        town TEXT NOT NULL,
        security_question TEXT NOT NULL,
        security_answer TEXT NOT NULL,
        date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print("SUCCESS: Users table rebuilt to handle security questions and answers!")