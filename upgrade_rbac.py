import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('maize_connect.db')

# 1. Destroy old admins table and rebuild with the 'role' column
conn.execute('DROP TABLE IF EXISTS admins')
conn.execute('''
    CREATE TABLE admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        province TEXT NOT NULL,
        security_question TEXT NOT NULL,
        security_answer_hash TEXT NOT NULL,
        role TEXT DEFAULT 'agent'
    )
''')

# 2. Automatically recreate YOU as the untouchable Main Admin
secure_hash = generate_password_hash('@2004Simari')
answer_hash = generate_password_hash('chinhoyi')

conn.execute('''
    INSERT INTO admins (username, password_hash, province, security_question, security_answer_hash, role) 
    VALUES (?, ?, ?, ?, ?, 'main_admin')
''', ('admin', secure_hash, 'Mashonaland West', 'What city were you born in?', answer_hash))

conn.commit()
conn.close()
print("SUCCESS: Vault upgraded for Roles. You are officially the Main Admin.")