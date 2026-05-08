import sqlite3
import os

db_path = os.path.join('instance', 'marketplace.db')

if not os.path.exists(db_path):
    # Try current directory
    db_path = 'marketplace.db'

print(f"Connecting to database at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add predicted_price to product
    try:
        cursor.execute("ALTER TABLE product ADD COLUMN predicted_price FLOAT;")
        print("Added predicted_price column.")
    except sqlite3.OperationalError:
        print("predicted_price column already exists.")

    # Add advisory to product
    try:
        cursor.execute("ALTER TABLE product ADD COLUMN advisory TEXT;")
        print("Added advisory column.")
    except sqlite3.OperationalError:
        print("advisory column already exists.")

    # Table MarketPrice will be created by db.create_all() automatically next time the app runs
    # but we can do it here too just in case
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_price (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_name VARCHAR(100) NOT NULL,
        price FLOAT NOT NULL,
        date DATE
    );
    """)
    print("Ensured market_price table exists.")

    conn.commit()
    conn.close()
    print("Migration successful!")
except Exception as e:
    print(f"Error during migration: {e}")
