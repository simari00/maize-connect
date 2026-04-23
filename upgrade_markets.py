import sqlite3

conn = sqlite3.connect('maize_connect.db')

# 1. Rebuild the market_prices table to allow multiple markets per province
conn.execute('DROP TABLE IF EXISTS market_prices')
conn.execute('''
    CREATE TABLE market_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        province TEXT NOT NULL,
        town TEXT NOT NULL,
        market_name TEXT NOT NULL,
        price_per_ton TEXT NOT NULL,
        date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(province, market_name) 
    )
''')

# 2. Inject demo data with specific towns
markets = [
    ('Harare', 'Harare City', 'GMB Aspindale', '390.00'),
    ('Mashonaland West', 'Chinhoyi', 'GMB Lions Den', '395.00'),
    ('Mashonaland West', 'Karoi', 'Karoi Grain Hub', '405.00'),
    ('Midlands', 'Gweru', 'GMB Gweru', '388.00'),
    ('Midlands', 'Kwekwe', 'Farmers Co-op', '390.00'),
    ('Bulawayo', 'Bulawayo City', 'GMB Belmont', '385.00')
]

for prov, town, name, price in markets:
    conn.execute('''
        INSERT INTO market_prices (province, town, market_name, price_per_ton) 
        VALUES (?, ?, ?, ?)
    ''', (prov, town, name, price))

conn.commit()
conn.close()
print("SUCCESS: Markets database upgraded for hyper-local town tracking!")