import sys
import sqlite3
import psycopg2
import random
from config import SUPABASE_CONN_STRING, LOCAL_OLTP_DATABASE, is_supabase_configured

# Realistic Countries & Cities mapping for enterprise retail stores
STORE_LOCATIONS = [
    ("Retail Hub - New York", "New York", "NY", "United States"),
    ("Retail Hub - Los Angeles", "Los Angeles", "CA", "United States"),
    ("Retail Hub - Chicago", "Chicago", "IL", "United States"),
    ("Retail Hub - Toronto", "Toronto", "ON", "Canada"),
    ("Retail Hub - Vancouver", "Vancouver", "BC", "Canada"),
    ("Retail Hub - London", "London", "Greater London", "United Kingdom"),
    ("Retail Hub - Manchester", "Manchester", "Lancashire", "United Kingdom"),
    ("Retail Hub - Berlin", "Berlin", "Berlin", "Germany"),
    ("Retail Hub - Munich", "Munich", "Bavaria", "Germany"),
    ("Retail Hub - Paris", "Paris", "Île-de-France", "France"),
    ("Retail Hub - Lyon", "Lyon", "Auvergne-Rhône-Alpes", "France"),
    ("Retail Hub - Sydney", "Sydney", "NSW", "Australia"),
    ("Retail Hub - Melbourne", "Melbourne", "VIC", "Australia"),
    ("Retail Hub - Tokyo", "Tokyo", "Kanto", "Japan"),
    ("Retail Hub - Mumbai", "Mumbai", "Maharashtra", "India"),
    ("Retail Hub - Delhi", "Delhi", "NCR", "India"),
    ("Retail Hub - Bangalore", "Bangalore", "Karnataka", "India"),
    ("Retail Hub - Mexico City", "Mexico City", "CDMX", "Mexico"),
    ("Retail Hub - Dubai", "Dubai", "Dubai", "United Arab Emirates"),
    ("Retail Hub - Beijing", "Beijing", "Beijing", "China")
]

FIRST_NAMES = [
    "Alex", "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Lucas", "Isabella",
    "Mason", "Mia", "Oliver", "Amelia", "Elijah", "Harper", "Logan", "Evelyn", "James", "Abigail",
    "Arjun", "Priya", "Aarav", "Ananya", "Rohan", "Diya", "Vihaan", "Isha", "Kavya", "Aditya",
    "Hans", "Frederik", "Greta", "Karl", "Heidi", "Jean", "Camille", "Louis", "Chloe", "Antoine",
    "Yuki", "Kenji", "Hana", "Ren", "Aoi", "Wei", "Ming", "Ling", "Jing", "Chen",
    "Carlos", "Sofia", "Mateo", "Valentina", "Diego", "Fatima", "Zaid", "Youssef", "Tariq", "Zahra"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Mehta", "Sharma", "Verma", "Patel", "Gupta", "Singh", "Mukherjee", "Reddy", "Nair", "Joshi",
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Dubois", "Bernard", "Thomas", "Petit", "Robert",
    "Tanaka", "Sato", "Suzuki", "Takahashi", "Watanabe", "Wang", "Li", "Zhang", "Liu", "Chen",
    "Gomez", "Lopez", "Gonzalez", "Hernandez", "Perez", "Al-Sayed", "Khan", "Ahmed", "Hassan", "Ali"
]

DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "retailcorp.org", "enterprise.io"]
TIERS = ["Platinum", "Gold", "Silver", "Bronze"]

def generate_realistic_customers(count=1000):
    """Generates a dataset of high-volume realistic customer profiles."""
    random.seed(42) # Deterministic generation
    customers = []
    seen_emails = set()

    for i in range(1, count + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        
        domain = random.choice(DOMAINS)
        email = f"{first.lower()}.{last.lower()}{i}@{domain}"
        if email in seen_emails:
            email = f"{first.lower()}{last.lower()}{i}_{random.randint(100,999)}@{domain}"
        seen_emails.add(email)

        # Pick matching country from store locations
        _, _, _, country = random.choice(STORE_LOCATIONS)
        tier = random.choice(TIERS)
        customers.append((name, email, country, tier))

    return customers

def setup_supabase_db(customers):
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

        print(f" -> Inserting {len(customers)} realistic customer records into Supabase Cloud DB...")
        for name, email, country, tier in customers:
            cursor.execute("""
                INSERT INTO customers (customer_name, email, country, membership_tier)
                VALUES (%s, %s, %s, %s)
            """, (name, email, country, tier))

        print(f" -> Inserting {len(STORE_LOCATIONS)} global store locations into Supabase...")
        for name, city, state, country in STORE_LOCATIONS:
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

def setup_local_sqlite_oltp(customers=None):
    """Initializes customer and store tables in local SQLite OLTP database."""
    print("==================================================")
    print("INITIALIZING HIGH-VOLUME ENTERPRISE SQLITE DATABASE (LOCAL OLTP)")
    print("==================================================\n")
    
    if customers is None:
        customers = generate_realistic_customers(1000)

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

    print(f" -> Inserting {len(customers)} high-volume realistic customer records...")
    for name, email, country, tier in customers:
        cursor.execute("""
            INSERT INTO customers (customer_name, email, country, membership_tier)
            VALUES (?, ?, ?, ?)
        """, (name, email, country, tier))

    print(f" -> Inserting {len(STORE_LOCATIONS)} retail store branch locations...")
    for name, city, state, country in STORE_LOCATIONS:
        cursor.execute("""
            INSERT INTO stores (store_name, city, state, country)
            VALUES (?, ?, ?, ?)
        """, (name, city, state, country))

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM customers;")
    count = cursor.fetchone()[0]
    print(f" -> Success! Configured {count} realistic customer records in local SQLite ({LOCAL_OLTP_DATABASE}).\n")
    cursor.close()
    conn.close()

def main():
    customers = generate_realistic_customers(1000)
    if is_supabase_configured():
        success = setup_supabase_db(customers)
        if not success:
            setup_local_sqlite_oltp(customers)
    else:
        print("[INFO] Supabase credentials not set or using placeholder URI.")
        setup_local_sqlite_oltp(customers)

if __name__ == "__main__":
    main()
