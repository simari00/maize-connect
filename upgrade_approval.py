import sqlite3

conn = sqlite3.connect('maize_connect.db')

try:
    conn.execute("ALTER TABLE admins ADD COLUMN status TEXT DEFAULT 'approved'")
    print("SUCCESS: Status column added. Approval workflow is ready.")
except sqlite3.OperationalError:
    print("Notice: Status column already exists.")

conn.commit()
conn.close()