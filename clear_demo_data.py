import sqlite3

conn = sqlite3.connect('maize_connect.db')

print("Starting database cleanup...")

# 1. Delete all records from the data tables
conn.execute('DELETE FROM market_prices')
conn.execute('DELETE FROM inputs')
conn.execute('DELETE FROM weather')

# Try to clear listings if you tested the USSD "Sell Maize" feature
try:
    conn.execute('DELETE FROM listings')
except sqlite3.OperationalError:
    pass

# 2. Reset the ID counters back to zero so your next entries start at ID #1
try:
    conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'market_prices'")
    conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'inputs'")
    conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'weather'")
    conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'listings'")
except sqlite3.OperationalError:
    pass

conn.commit()
conn.close()

print("SUCCESS: All demo data has been wiped! Your system is clean and ready for real data.")