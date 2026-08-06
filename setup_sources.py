import sys
import sqlite3
import psycopg2
from config import SUPABASE_CONN_STRING, LOCAL_OLTP_DATABASE, is_supabase_configured

SAMPLE_CUSTOMERS = [
    ("John Doe", "john.doe@example.com", "United States", "Gold"),
    ("Jane Smith", "jane.smith@example.com", "Canada", "Silver"),
    ("Arjun Mehta", "arjun.mehta@example.com", "India", "Gold"),
    ("Sophie Dubois", "sophie.dubois@example.com", "France", "Bronze"),
    ("Yuki Tanaka", "yuki.tanaka@example.com", "Germany", "Silver"),
    ("Carlos Gomez", "carlos.gomez@example.com", "Mexico", "Bronze"),
    ("Sarah Jenkins", "sarah.j@example.com", "United Kingdom", "Gold"),
    ("Hans Müller", "hans.mueller@example.com", "Germany", "Silver"),
    ("Fatima Al-Sayed", "fatima.s@example.com", "United Arab Emirates", "Gold"),
    ("Chen Wei", "chen.wei@example.com", "China", "Bronze"),
    ("Liam Wilson", "liam.w@example.com", "Australia", "Silver")
]

SAMPLE_STORES = [
    ("Retail Hub - New York", "New York", "NY", "United States"),
    ("Retail Hub - Toronto", "Toronto", "ON", "Canada"),
    ("Retail Hub - London", "London", "Greater London", "United Kingdom"),
    ("Retail Hub - Berlin", "Berlin", "Berlin", "Germany"),
    ("Retail Hub - Paris", "Paris", "Île-de-France", "France"),
    ("Retail Hub - Sydney", "Sydney", "NSW", "Australia")
]

def setup_supabase_db():
    """Initializes customer and store tables in Cloud PostgreSQL (Supabase)."""
    print("==================================================")
    print("INITIALIZING SUPABASE ONLINE DATABASE SOURCE (CLOUD OLTP)")
    print("==================================================\n")
    
    try:
        print(" -> Connecting to Supabase online PostgreSQL database...")
        conn = psycopg2.connect(SUPABASE_CONN_STRING)
        cursor = conn.cursor()
        print(" -> Connected successfully!")

        print(" -> Recreating 'customers' & 'stores' tables in Supabase...")
        cursor.execute("DROP TABLE IF EXISTS customers CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS stores CASCADE;")

        cursor.execute("""
            CREATE TABLE customers (
                customer_id SERIAL PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                country VARCHAR(50) NOT NULL,
                membership_tier VARCHAR(20) NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE stores (
                store_id SERIAL PRIMARY KEY,
                store_name VARCHAR(100) NOT NULL,
                city VARCHAR(50) NOT NULL,
                state VARCHAR(50) NOT NULL,
                country VARCHAR(50) NOT NULL
            );
        """)

        print(f" -> Inserting {len(SAMPLE_CUSTOMERS)} customer records into Supabase...")
        for name, email, country, tier in SAMPLE_CUSTOMERS:
            cursor.execute("""
                INSERT INTO customers (customer_name, email, country, membership_tier)
                VALUES (%s, %s, %s, %s)
            """, (name, email, country, tier))

        print(f" -> Inserting {len(SAMPLE_STORES)} store records into Supabase...")
        for name, city, state, country in SAMPLE_STORES:
            cursor.execute("""
                INSERT INTO stores (store_name, city, state, country)
                VALUES (%s, %s, %s, %s)
            """, (name, city, state, country))

        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM customers;")
        count = cursor.fetchone()[0]
        print(f" -> Success! Configured {count} customer records in Supabase Cloud DB.\n")
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"\n[WARNING] Supabase cloud connection failed: {e}")
        print("Falling back to local SQLite OLTP database...\n")
        return False

def setup_local_sqlite_oltp():
    """Initializes customer and store tables in local SQLite OLTP database."""
    print("==================================================")
    print("INITIALIZING LOCAL SQLITE DATABASE SOURCE (LOCAL OLTP FALLBACK)")
    print("==================================================\n")
    
    conn = sqlite3.connect(LOCAL_OLTP_DATABASE)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS customers;")
    cursor.execute("DROP TABLE IF EXISTS stores;")

    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            country TEXT NOT NULL,
            membership_tier TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE stores (
            store_id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            country TEXT NOT NULL
        );
    """)

    for name, email, country, tier in SAMPLE_CUSTOMERS:
        cursor.execute("""
            INSERT INTO customers (customer_name, email, country, membership_tier)
            VALUES (?, ?, ?, ?)
        """, (name, email, country, tier))

    for name, city, state, country in SAMPLE_STORES:
        cursor.execute("""
            INSERT INTO stores (store_name, city, state, country)
            VALUES (?, ?, ?, ?)
        """, (name, city, state, country))

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM customers;")
    count = cursor.fetchone()[0]
    print(f" -> Success! Configured {count} customer records in local SQLite ({LOCAL_OLTP_DATABASE}).\n")
    cursor.close()
    conn.close()

def main():
    if is_supabase_configured():
        success = setup_supabase_db()
        if not success:
            setup_local_sqlite_oltp()
    else:
        print("[INFO] Supabase credentials not set or using placeholder URI.")
        setup_local_sqlite_oltp()

if __name__ == "__main__":
    main()
