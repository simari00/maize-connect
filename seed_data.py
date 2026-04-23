import sqlite3

# Connect to the database
conn = sqlite3.connect('maize_connect.db')

# 1. Realistic Market Data for all 10 Provinces
market_data = [
    ('Harare', 'Harare', 'GMB Aspindale', '390.00'),
    ('Bulawayo', 'Bulawayo', 'GMB Belmont', '385.00'),
    ('Manicaland', 'Mutare', 'GMB Mutare', '380.00'),
    ('Midlands', 'Gweru', 'GMB Gweru', '388.00'),
    ('Masvingo', 'Masvingo', 'GMB Masvingo', '392.00'),
    ('Mashonaland West', 'Chinhoyi', 'GMB Lions Den', '395.00'),
    ('Mashonaland Central', 'Bindura', 'GMB Bindura', '390.00'),
    ('Mashonaland East', 'Marondera', 'GMB Marondera', '385.00'),
    ('Matabeleland South', 'Gwanda', 'GMB Gwanda', '400.00'),
    ('Matabeleland North', 'Lupane', 'GMB Lupane', '398.00')
]

# 2. Realistic Farming Inputs for all 10 Provinces
input_data = [
    ('Harare', 'Harare', 'Farm & City', 'SeedCo SC510 - 25kg', '115.00'),
    ('Bulawayo', 'Bulawayo', 'Agri-Value', 'FSG Fertilizer - 50kg', '45.00'),
    ('Manicaland', 'Mutare', 'Farmers Co-op', 'Pioneer Seed - 10kg', '35.00'),
    ('Midlands', 'Gweru', 'Agri-Seeds', 'Ammonium Nitrate - 50kg', '50.00'),
    ('Masvingo', 'Masvingo', 'Farm & City', 'Compound D - 50kg', '42.00'),
    ('Mashonaland West', 'Chinhoyi', 'ZFC Limited', 'SeedCo SC719 - 25kg', '120.00'),
    ('Mashonaland Central', 'Bindura', 'Omnia', 'Urea Fertilizer - 50kg', '48.00'),
    ('Mashonaland East', 'Marondera', 'Farm Supply', 'Kutsaga Seed - 10kg', '30.00'),
    ('Matabeleland South', 'Gwanda', 'Agro-Vet', 'Sorghum Seed - 10kg', '25.00'),
    ('Matabeleland North', 'Lupane', 'Farmers Market', 'Cowpeas Seed - 5kg', '15.00')
]

# 3. Inject the data using INSERT OR REPLACE (to avoid duplicates if run twice)
conn.executemany('''
    INSERT OR REPLACE INTO market_prices (province, town, market_name, price_per_ton) 
    VALUES (?, ?, ?, ?)
''', market_data)

conn.executemany('''
    INSERT OR REPLACE INTO inputs (province, town, supplier_name, item_name, price) 
    VALUES (?, ?, ?, ?, ?)
''', input_data)

conn.commit()
conn.close()

print("SUCCESS: Database fully populated with national agricultural demo data!")