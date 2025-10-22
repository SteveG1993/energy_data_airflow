"""
SQLite Database Setup Script
Creates a SQLite database for storing custom data
"""

import sqlite3
import os

# Database configuration
DB_PATH = '/Users/stevengregoire/airflow/my_data.db'

def create_database():
    """Create SQLite database and example tables"""

    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Creating database at: {DB_PATH}")

    # Example table 1: Users data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Created 'users' table")

    # Example table 2: Data records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_name TEXT NOT NULL,
            record_value TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Created 'data_records' table")

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print(f"\n✓ Database created successfully!")
    print(f"Location: {DB_PATH}")
    print(f"Size: {os.path.getsize(DB_PATH)} bytes")

def insert_sample_data():
    """Insert some sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert sample users
    sample_users = [
        ('steve', 'steve@example.com'),
        ('admin', 'admin@example.com')
    ]

    cursor.executemany(
        'INSERT OR IGNORE INTO users (username, email) VALUES (?, ?)',
        sample_users
    )

    # Insert sample records
    sample_records = [
        ('Test Record 1', 'Sample Value 1', 'Category A'),
        ('Test Record 2', 'Sample Value 2', 'Category B'),
    ]

    cursor.executemany(
        'INSERT INTO data_records (record_name, record_value, category) VALUES (?, ?, ?)',
        sample_records
    )

    conn.commit()
    conn.close()

    print("\n✓ Sample data inserted")

def view_data():
    """View data in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n--- Users Table ---")
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Created: {user[3]}")

    print("\n--- Data Records Table ---")
    cursor.execute('SELECT * FROM data_records')
    records = cursor.fetchall()
    for record in records:
        print(f"ID: {record[0]}, Name: {record[1]}, Value: {record[2]}, Category: {record[3]}")

    conn.close()

if __name__ == '__main__':
    print("SQLite Database Setup\n" + "="*50)

    # Create database and tables
    create_database()

    # Ask if user wants sample data
    response = input("\nWould you like to insert sample data? (y/n): ")
    if response.lower() == 'y':
        insert_sample_data()
        view_data()

    print("\n" + "="*50)
    print("Database setup complete!")
    print(f"\nTo connect to this database in your DAGs, use:")
    print(f"  conn = sqlite3.connect('{DB_PATH}')")
