import sqlite3

# Connect directly to the database Flask is using
conn = sqlite3.connect('maize_connect.db')

try:
    # Forcefully inject the new column into the existing table
    conn.execute("ALTER TABLE listings ADD COLUMN status TEXT DEFAULT 'OPEN'")
    print("SUCCESS: The 'status' column has been successfully injected!")
except sqlite3.OperationalError as e:
    print(f"Notice: {e} (This usually means the column is already there)")

conn.commit()
conn.close()