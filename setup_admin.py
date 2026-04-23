import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('maize_connect.db')

# 1. Destroy the old table to force the upgrade
conn.execute('DROP TABLE IF EXISTS admins')

# 2. Create the UPGRADED secure admins table
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

# 3. Generate hashes for the Master Admin
secure_hash = generate_password_hash('@2004Simari')
answer_hash = generate_password_hash('chinhoyi') # Lowercase answer for the security question

try:
    # Insert the Master Admin
    conn.execute('''
        INSERT INTO admins (username, password_hash, province, security_question, security_answer_hash) 
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin', secure_hash, 'Mashonaland West', 'What city were you born in?', answer_hash))
    
    print("SUCCESS: Advanced Admin vault secured. Username: 'admin' | Password: '@2004Simari'")
except sqlite3.IntegrityError:
    print("Notice: Admin account already exists in the vault.")

conn.commit()
conn.close()