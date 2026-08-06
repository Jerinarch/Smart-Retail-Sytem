import sys
import sqlite3
import psycopg2
import requests
import io
import urllib3
import ssl
import pandas as pd
from config import SUPABASE_CONN_STRING, LOCAL_OLTP_DATABASE, is_supabase_configured

# Disable SSL warnings for external network compatibility
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

KAGGLE_SUPERSTORE_CSV_URL = "https://raw.githubusercontent.com/PacktPublishing/Learning-Tableau-10/master/Chapter%2001/Superstore.csv"

def fetch_kaggle_superstore_dataset():
    """Fetches and extracts unique customer & store profiles from Kaggle Superstore dataset."""
    print(f" -> Ingesting Kaggle Superstore Dataset from ({KAGGLE_SUPERSTORE_CSV_URL})...")
    try:
        response = requests.get(KAGGLE_SUPERSTORE_CSV_URL, verify=False, timeout=15)
        if response.status_code == 200:
            df_raw = pd.read_csv(io.BytesIO(response.content), encoding="windows-1252")
            print(f"   * Downloaded Kaggle Superstore dataset ({len(df_raw)} records). Processing dimensions...")

            # 1. Extract Unique Customer Profiles
            df_cust_unique = df_raw.drop_duplicates(subset=["Customer Name"]).copy()
            countries = ["United States", "Canada", "United Kingdom", "Germany", "France", "Australia"]
            segment_tier_map = {
                "Corporate": "Platinum",
                "Consumer": "Gold",
                "Home Office": "Silver"
            }

            customers = []
            seen_emails = set()

            for idx, row in df_cust_unique.iterrows():
                name = str(row["Customer Name"]).strip()
                names = name.split()
                first = names[0].lower() if len(names) > 0 else "user"
                last = names[-1].lower() if len(names) > 1 else "cust"
                
                email = f"{first}.{last}@superstore.com"
                if email in seen_emails:
                    email = f"{first}.{last}{idx}@superstore.com"
                seen_emails.add(email)

                country = countries[idx % len(countries)]
                raw_segment = str(row.get("Customer Segment", "Consumer")).strip()
                tier = segment_tier_map.get(raw_segment, "Gold")
                
                customers.append((name, email, country, tier))

            # 2. Extract Unique Store Outlet Profiles
            df_stores_unique = df_raw.drop_duplicates(subset=["City", "State"]).head(50).copy()
            stores = []
            for idx, row in df_stores_unique.iterrows():
                city = str(row["City"]).strip()
                state = str(row["State"]).strip()
                country = countries[idx % len(countries)]
                store_name = f"Superstore Hub - {city}"
                stores.append((store_name, city, state, country))

            print(f"   * Extracted {len(customers)} unique real customer profiles & {len(stores)} store locations.")
            return customers, stores
        else:
            raise Exception(f"HTTP Status Code {response.status_code}")

    except Exception as e:
        print(f"   * Kaggle dataset fetch failed ({e}). Loading fallback customer profiles...")
        backup_customers = [
            ("Claire Gute", "claire.gute@superstore.com", "United States", "Platinum"),
            ("Brosina Hoffman", "brosina.hoffman@superstore.com", "Canada", "Gold"),
            ("Andrew Allen", "andrew.allen@superstore.com", "United Kingdom", "Silver"),
            ("Irene Maddox", "irene.maddox@superstore.com", "Germany", "Gold"),
            ("Harold Pawlan", "harold.pawlan@superstore.com", "France", "Bronze"),
            ("Pete Kious", "pete.kious@superstore.com", "Australia", "Platinum")
        ]
        backup_stores = [
            ("Superstore Hub - Los Angeles", "Los Angeles", "CA", "United States"),
            ("Superstore Hub - Toronto", "Toronto", "ON", "Canada"),
            ("Superstore Hub - London", "London", "Greater London", "United Kingdom"),
            ("Superstore Hub - Berlin", "Berlin", "Berlin", "Germany"),
            ("Superstore Hub - Paris", "Paris", "Île-de-France", "France"),
            ("Superstore Hub - Sydney", "Sydney", "NSW", "Australia")
        ]
        return backup_customers, backup_stores

def setup_supabase_db(customers, stores):
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

        print(f" -> Ingesting {len(customers)} Kaggle customer records into Supabase Cloud DB...")
        for name, email, country, tier in customers:
            cursor.execute("""
                INSERT INTO customers (customer_name, email, country, membership_tier)
                VALUES (%s, %s, %s, %s)
            """, (name, email, country, tier))

        print(f" -> Ingesting {len(stores)} Kaggle store locations into Supabase...")
        for name, city, state, country in stores:
            cursor.execute("""
                INSERT INTO stores (store_name, city, state, country)
                VALUES (%s, %s, %s, %s)
            """, (name, city, state, country))

        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM customers;")
        count = cursor.fetchone()[0]
        print(f" -> Success! Ingested {count} Kaggle customer profiles into Supabase Cloud DB.\n")
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"\n[WARNING] Supabase cloud connection failed: {e}")
        print("Falling back to local SQLite OLTP database...\n")
        return False

def setup_local_sqlite_oltp(customers=None, stores=None):
    """Initializes customer and store tables in local SQLite OLTP database."""
    print("==================================================")
    print("INITIALIZING KAGGLE SUPERSTORE OLTP DATABASE (LOCAL SQLITE SOURCE)")
    print("==================================================\n")
    
    if customers is None or stores is None:
        customers, stores = fetch_kaggle_superstore_dataset()

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

    print(f" -> Ingesting {len(customers)} Kaggle customer profiles into local OLTP database...")
    for name, email, country, tier in customers:
        cursor.execute("""
            INSERT INTO customers (customer_name, email, country, membership_tier)
            VALUES (?, ?, ?, ?)
        """, (name, email, country, tier))

    print(f" -> Ingesting {len(stores)} Kaggle store outlet locations into local OLTP database...")
    for name, city, state, country in stores:
        cursor.execute("""
            INSERT INTO stores (store_name, city, state, country)
            VALUES (?, ?, ?, ?)
        """, (name, city, state, country))

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM customers;")
    count = cursor.fetchone()[0]
    print(f" -> Success! Configured {count} Kaggle customer profiles in local SQLite ({LOCAL_OLTP_DATABASE}).\n")
    cursor.close()
    conn.close()

def main():
    customers, stores = fetch_kaggle_superstore_dataset()
    if is_supabase_configured():
        success = setup_supabase_db(customers, stores)
        if not success:
            setup_local_sqlite_oltp(customers, stores)
    else:
        print("[INFO] Supabase credentials not set or using placeholder URI.")
        setup_local_sqlite_oltp(customers, stores)

if __name__ == "__main__":
    main()
