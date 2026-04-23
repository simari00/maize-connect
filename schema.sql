-- New National schema.sql (Fixed Constraints)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    pin TEXT NOT NULL,
    province TEXT NOT NULL,
    town TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    province TEXT NOT NULL,
    town TEXT UNIQUE NOT NULL,
    market_name TEXT NOT NULL,
    price_per_ton TEXT NOT NULL,
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    province TEXT NOT NULL,
    town TEXT UNIQUE NOT NULL,
    forecast TEXT NOT NULL,
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    province TEXT NOT NULL,
    town TEXT UNIQUE NOT NULL,
    supplier_name TEXT NOT NULL,
    item_name TEXT NOT NULL,
    price TEXT NOT NULL,
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL,
    province TEXT NOT NULL,
    town TEXT NOT NULL,
    quantity_tons TEXT NOT NULL,
    price_per_ton TEXT NOT NULL,
    date_listed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL,
    province TEXT NOT NULL,
    town TEXT NOT NULL,
    quantity_tons TEXT NOT NULL,
    price_per_ton TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN', 
    date_listed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL,
    province TEXT NOT NULL,
    town TEXT NOT NULL,
    quantity_tons TEXT NOT NULL,
    price_per_ton TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN', 
    date_listed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);