import sqlite3

conn = sqlite3.connect('maize_connect.db')

conn.execute('DROP TABLE IF EXISTS weather')
conn.execute('''
    CREATE TABLE weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        province TEXT UNIQUE NOT NULL,
        town TEXT NOT NULL,
        forecast TEXT NOT NULL,
        outlook TEXT NOT NULL,
        date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print("SUCCESS: Weather table upgraded to handle API-driven long-term outlooks!")