import sqlite3
import os

db_file = 'maize_connect.db'

# Delete the old database if it still exists
if os.path.exists(db_file):
    os.remove(db_file)
    print("Old database deleted.")

# Create the new database and run the schema
connection = sqlite3.connect(db_file)
with open('schema.sql') as f:
    connection.executescript(f.read())
    
connection.commit()
connection.close()
print("New National Database built successfully. You are ready.")