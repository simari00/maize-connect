import sqlite3

conn = sqlite3.connect('maize_connect.db')

# 1. Rebuild Market Prices Table
conn.execute('DROP TABLE IF EXISTS market_prices')
conn.execute('''
    CREATE TABLE market_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        province TEXT UNIQUE NOT NULL,
        town TEXT NOT NULL,
        market_name TEXT NOT NULL,
        price_per_ton TEXT NOT NULL,
        date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# 2. Rebuild Inputs Table
conn.execute('DROP TABLE IF EXISTS inputs')
conn.execute('''
    CREATE TABLE inputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        province TEXT UNIQUE NOT NULL,
        town TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        item_name TEXT NOT NULL,
        price TEXT NOT NULL,
        date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

print("SUCCESS: Tables rebuilt. Province is now the primary key!")
conn.commit()
conn.close()