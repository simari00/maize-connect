import os
import psycopg2
from werkzeug.security import generate_password_hash

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("This script is only for the live Render PostgreSQL database.")
    exit()

conn = psycopg2.connect(db_url)
cursor = conn.cursor()

print("Building exact cloud replica of maize_connect.db...")

# 1. Admins Table
cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY, 
    username TEXT UNIQUE NOT NULL, 
    password_hash TEXT NOT NULL,
    province TEXT NOT NULL, 
    security_question TEXT NOT NULL, 
    security_answer_hash TEXT NOT NULL,
    role TEXT DEFAULT 'agent', 
    status TEXT DEFAULT 'approved'
)''')

# 2. Inputs Table
cursor.execute('''CREATE TABLE IF NOT EXISTS inputs (
    id SERIAL PRIMARY KEY, 
    province TEXT NOT NULL, 
    town TEXT NOT NULL, 
    supplier_name TEXT NOT NULL,
    item_name TEXT NOT NULL, 
    price TEXT NOT NULL, 
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    UNIQUE(province, item_name)
)''')

# 3. Listings Table
cursor.execute('''CREATE TABLE IF NOT EXISTS listings (
    id SERIAL PRIMARY KEY, 
    phone_number TEXT NOT NULL, 
    province TEXT NOT NULL, 
    town TEXT NOT NULL,
    quantity_tons TEXT NOT NULL, 
    price_per_ton TEXT NOT NULL, 
    date_listed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'OPEN'
)''')

# 4. Market Prices Table
cursor.execute('''CREATE TABLE IF NOT EXISTS market_prices (
    id SERIAL PRIMARY KEY, 
    province TEXT NOT NULL, 
    town TEXT NOT NULL, 
    market_name TEXT NOT NULL,
    price_per_ton TEXT NOT NULL, 
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    UNIQUE(province, market_name)
)''')

# 5. Users Table
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY, 
    phone_number TEXT UNIQUE NOT NULL, 
    full_name TEXT NOT NULL,
    pin TEXT NOT NULL, 
    province TEXT NOT NULL, 
    town TEXT NOT NULL, 
    security_question TEXT NOT NULL,
    security_answer TEXT NOT NULL, 
    date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# 6. Weather Table
cursor.execute('''CREATE TABLE IF NOT EXISTS weather (
    id SERIAL PRIMARY KEY, 
    province TEXT UNIQUE NOT NULL, 
    town TEXT NOT NULL, 
    forecast TEXT NOT NULL,
    outlook TEXT NOT NULL, 
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# 7. Create the Master Admin safely
secure_hash = generate_password_hash('@2004Simari')
answer_hash = generate_password_hash('chinhoyi')
cursor.execute('''INSERT INTO admins (username, password_hash, province, security_question, security_answer_hash, role, status) 
    VALUES (%s, %s, %s, %s, %s, 'main_admin', 'approved') ON CONFLICT DO NOTHING''', 
    ('admin', secure_hash, 'Mashonaland West', 'What city were you born in?', answer_hash))

conn.commit()
conn.close()
print("SUCCESS: 1-to-1 PostgreSQL Database Replica is ready for production!")