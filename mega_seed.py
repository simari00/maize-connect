import sqlite3

conn = sqlite3.connect('maize_connect.db')

# 1. Rebuild the table to allow multiple items per province
conn.execute('DROP TABLE IF EXISTS inputs')
conn.execute('''
    CREATE TABLE inputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        province TEXT NOT NULL,
        town TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        item_name TEXT NOT NULL,
        price TEXT NOT NULL,
        date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(province, item_name) 
    )
''')

# 2. The Full Agricultural Catalog
provinces = [
    ('Harare', 'Harare'), ('Bulawayo', 'Bulawayo'), ('Manicaland', 'Mutare'), 
    ('Midlands', 'Gweru'), ('Masvingo', 'Masvingo'), ('Mashonaland West', 'Chinhoyi'),
    ('Mashonaland Central', 'Bindura'), ('Mashonaland East', 'Marondera'), 
    ('Matabeleland South', 'Gwanda'), ('Matabeleland North', 'Lupane')
]

# Seeds, Fertilizer, Machinery, Irrigation, Pesticides, Tools
items = [
    ('SeedCo', 'SC719 Maize Seed 25kg', '120.00'),
    ('ZFC Limited', 'Ammonium Nitrate 50kg', '45.00'),
    ('William Bain', '2-Row Tractor Planter', '850.00'),
    ('DripTech', 'Drip Kit 1-Hectare', '320.00'),
    ('Agricura', 'Lambda Insecticide 1L', '15.00'),
    ('Zimplow', 'Crocodile Hoe (Badza)', '8.50')
]

# 3. Inject all 60 records
for prov, town in provinces:
    for supp, item, price in items:
        conn.execute('''
            INSERT INTO inputs (province, town, supplier_name, item_name, price) 
            VALUES (?, ?, ?, ?, ?)
        ''', (prov, town, supp, item, price))

conn.commit()
conn.close()
print("SUCCESS: 60 Input records injected across all 10 provinces!")