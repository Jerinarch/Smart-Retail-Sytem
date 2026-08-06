import sqlite3
import psycopg2
import pandas as pd
import requests
import hashlib
import urllib3
import ssl
import sys
import os
from config import (
    SUPABASE_CONN_STRING,
    DWH_DATABASE,
    LOCAL_OLTP_DATABASE,
    FAKESTORE_API_URL,
    GITHUB_SALES_CSV_URL,
    is_supabase_configured
)

# Disable SSL warnings for external network compatibility
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

def get_deterministic_product_key(name: str, max_keys: int) -> int:
    """Computes a 100% deterministic product key using MD5 cryptographic hashing."""
    if max_keys <= 0:
        return 1
    raw_hash = hashlib.md5(str(name).encode("utf-8")).hexdigest()
    hash_int = int(raw_hash, 16)
    return (hash_int % max_keys) + 1

def extract_customers_and_stores():
    """Extracts customer and store records from Supabase Postgres or local SQLite."""
    print(" -> Extracting Customers & Stores from OLTP Source...")
    if is_supabase_configured():
        try:
            conn = psycopg2.connect(SUPABASE_CONN_STRING)
            df_cust = pd.read_sql_query("SELECT * FROM customers", conn)
            df_stores = pd.read_sql_query("SELECT * FROM stores", conn)
            conn.close()
            print(f"   * Extracted {len(df_cust)} customers and {len(df_stores)} stores from Supabase Cloud DB.")
            return df_cust, df_stores
        except Exception as e:
            print(f"   * Supabase Cloud extract failed ({e}). Falling back to local SQLite...")
    
    # Fallback to local SQLite OLTP
    if not os.path.exists(LOCAL_OLTP_DATABASE):
        raise FileNotFoundError(
            f"OLTP database '{LOCAL_OLTP_DATABASE}' not found. Run 'python setup_sources.py' first!"
        )
    
    conn = sqlite3.connect(LOCAL_OLTP_DATABASE)
    df_cust = pd.read_sql_query("SELECT * FROM customers", conn)
    df_stores = pd.read_sql_query("SELECT * FROM stores", conn)
    conn.close()
    print(f"   * Extracted {len(df_cust)} customers and {len(df_stores)} stores from Local SQLite DB.")
    return df_cust, df_stores

def extract_product_catalog():
    """Extracts live products from FakeStore REST API (with local fallback)."""
    print(f" -> Fetching Product Catalog from REST API ({FAKESTORE_API_URL})...")
    try:
        response = requests.get(FAKESTORE_API_URL, verify=False, timeout=10)
        if response.status_code == 200:
            products_json = response.json()
            df_products = pd.DataFrame(products_json)
            print(f"   * Extracted {len(df_products)} products live from REST API.")
            return df_products
        else:
            raise Exception(f"HTTP Status Code {response.status_code}")
    except Exception as e:
        print(f"   * API request failed ({e}). Generating fallback product catalog...")
        fallback_data = [
            {"id": i, "title": f"Product Item {i}", "price": round(19.99 + i * 5.5, 2), "category": "Electronics" if i % 2 == 0 else "Clothing"}
            for i in range(1, 21)
        ]
        return pd.DataFrame(fallback_data)

def extract_sales_transactions():
    """Extracts historical sales transaction dataset from GitHub CSV repository."""
    print(" -> Downloading Sales Transactions ledger from GitHub CSV repository...")
    try:
        df_sales = pd.read_csv(GITHUB_SALES_CSV_URL)
        print(f"   * Extracted {len(df_sales)} raw sales transaction records.")
        return df_sales
    except Exception as e:
        print(f"   * CSV download failed ({e}). Generating synthetic fallback ledger...")
        import numpy as np
        dates = pd.date_range(start="2023-01-01", end="2025-12-31", freq="D")
        countries = ["United States", "Canada", "India", "France", "Germany", "United Kingdom"]
        products = [f"Product Item {i}" for i in range(1, 21)]
        
        synthetic_records = []
        for i in range(1, 1001):
            d = np.random.choice(dates)
            c = np.random.choice(countries)
            p = np.random.choice(products)
            qty = np.random.randint(1, 10)
            price = round(np.random.uniform(15.0, 150.0), 2)
            synthetic_records.append({
                "Date": pd.Timestamp(d).strftime("%Y-%m-%d"),
                "Country": c,
                "Product": p,
                "Order_Quantity": qty,
                "Unit_Price": price
            })
        return pd.DataFrame(synthetic_records)

def run_etl():
    """Main ETL Pipeline execution function following Medallion Architecture."""
    print("==================================================")
    print("STARTING MEDALLION ETL PIPELINE (RAW -> SILVER -> STAR SCHEMA)")
    print("==================================================\n")

    # -------------------------------------------------
    # PHASE 1: EXTRACTION (BRONZE LAYER)
    # -------------------------------------------------
    print("[PHASE 1: EXTRACTION (BRONZE LAYER)]")
    df_customers_raw, df_stores_raw = extract_customers_and_stores()
    df_products_raw = extract_product_catalog()
    df_sales_raw = extract_sales_transactions()
    print("Extraction Phase Completed.\n")

    # -------------------------------------------------
    # PHASE 2: TRANSFORMATION (SILVER LAYER)
    # -------------------------------------------------
    print("[PHASE 2: TRANSFORMATION & CONFORMED KEY INTEGRATION]")
    
    # A. Dim_Customers Transformation
    df_customers = df_customers_raw.copy()
    df_customers = df_customers.drop_duplicates(subset=["customer_id"])
    df_customers["customer_name"] = df_customers["customer_name"].astype(str).str.strip().str.title()
    df_customers["email"] = df_customers["email"].astype(str).str.strip().str.lower()
    df_customers["country"] = df_customers["country"].astype(str).str.strip().str.title()
    df_customers = df_customers.rename(columns={"customer_id": "customer_key"})
    df_customers = df_customers[["customer_key", "customer_name", "email", "country", "membership_tier"]]
    print(" -> Transformed Dimension: Dim_Customers")

    # B. Dim_Products Transformation
    df_products = df_products_raw.copy()
    df_products = df_products.drop_duplicates(subset=["id"])
    df_products = df_products.rename(columns={
        "id": "product_key",
        "title": "product_name",
        "price": "unit_price",
        "category": "category"
    })
    df_products["product_name"] = df_products["product_name"].astype(str).str.strip()
    df_products["category"] = df_products["category"].astype(str).str.strip().str.title()
    df_products["unit_cost"] = (df_products["unit_price"] * 0.65).round(2)
    df_products = df_products[["product_key", "product_name", "category", "unit_price", "unit_cost"]]
    print(" -> Transformed Dimension: Dim_Products")

    # C. Dim_Stores Transformation
    df_stores = df_stores_raw.copy()
    df_stores = df_stores.rename(columns={"store_id": "store_key"})
    df_stores = df_stores[["store_key", "store_name", "city", "state", "country"]]
    print(" -> Transformed Dimension: Dim_Stores")

    # D. Dim_Time Transformation
    df_sales_src = df_sales_raw.copy()
    df_sales_src["parsed_date"] = pd.to_datetime(df_sales_src["Date"])
    unique_dates = df_sales_src["parsed_date"].dropna().unique()
    
    time_records = []
    for d in unique_dates:
        dt = pd.Timestamp(d)
        time_records.append({
            "time_key": dt.strftime("%Y-%m-%d"),
            "day": dt.day,
            "month": dt.month,
            "year": dt.year,
            "quarter": (dt.month - 1) // 3 + 1,
            "day_of_week": dt.strftime("%A"),
            "is_weekend": dt.weekday() >= 5
        })
    df_time = pd.DataFrame(time_records)
    print(" -> Transformed Dimension: Dim_Time")

    # E. Fact_Sales Integration & Conformed Key Derivation
    df_sales = df_sales_src.copy()
    
    # 1. Map Country from CSV to Customer Key
    country_to_customer = df_customers.drop_duplicates(subset=["country"]).set_index("country")["customer_key"].to_dict()
    df_sales["customer_key"] = df_sales["Country"].astype(str).str.strip().str.title().map(country_to_customer)
    
    # 2. Cryptographic MD5 Hash mapping for deterministic product key conformation across sessions
    num_products = max(len(df_products), 1)
    df_sales["product_key"] = df_sales["Product"].apply(
        lambda name: get_deterministic_product_key(name, num_products)
    )
    
    # 3. Map Country to Store Key
    country_to_store = df_stores.drop_duplicates(subset=["country"]).set_index("country")["store_key"].to_dict()
    df_sales["store_key"] = df_sales["Country"].astype(str).str.strip().str.title().map(country_to_store)
    df_sales["store_key"] = df_sales["store_key"].fillna(1).astype(int)

    # 4. Form Time Key and Financial Metrics
    df_sales["time_key"] = df_sales["parsed_date"].dt.strftime("%Y-%m-%d")
    df_sales = df_sales.rename(columns={
        "Order_Quantity": "quantity",
        "Unit_Price": "unit_price"
    })
    
    # Fill defaults if missing
    df_sales["quantity"] = df_sales["quantity"].fillna(1).astype(int)
    df_sales["unit_price"] = df_sales["unit_price"].fillna(25.0).astype(float)
    
    # Financial facts calculation
    df_sales["total_revenue"] = (df_sales["quantity"] * df_sales["unit_price"]).round(2)
    df_sales["total_profit"] = (df_sales["total_revenue"] * 0.35).round(2)
    
    # Transaction ID generation
    df_sales["transaction_id"] = [f"TXN{i:06d}" for i in range(1, len(df_sales) + 1)]
    
    # Drop records missing essential dimension links
    df_sales = df_sales.dropna(subset=["customer_key", "product_key", "time_key"])
    df_sales["customer_key"] = df_sales["customer_key"].astype(int)
    df_sales["product_key"] = df_sales["product_key"].astype(int)
    
    df_sales = df_sales[[
        "transaction_id", "customer_key", "product_key", "store_key", "time_key",
        "quantity", "unit_price", "total_revenue", "total_profit"
    ]]
    print(f" -> Integrated Fact Table: Fact_Sales ({len(df_sales)} transactions)")
    print("Transformation Phase Completed.\n")

    # -------------------------------------------------
    # PHASE 3: LOADING (GOLD STAR SCHEMA DATA WAREHOUSE)
    # -------------------------------------------------
    print(f"[PHASE 3: LOADING INTO DATA WAREHOUSE ({DWH_DATABASE})]")
    conn_dwh = sqlite3.connect(DWH_DATABASE)
    cursor = conn_dwh.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS Fact_Sales;")
    cursor.execute("DROP TABLE IF EXISTS Dim_Customers;")
    cursor.execute("DROP TABLE IF EXISTS Dim_Products;")
    cursor.execute("DROP TABLE IF EXISTS Dim_Stores;")
    cursor.execute("DROP TABLE IF EXISTS Dim_Time;")

    # DDL: Dimension Tables
    cursor.execute("""
        CREATE TABLE Dim_Customers (
            customer_key INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            country TEXT NOT NULL,
            membership_tier TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE Dim_Products (
            product_key INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_price REAL NOT NULL,
            unit_cost REAL NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE Dim_Stores (
            store_key INTEGER PRIMARY KEY,
            store_name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            country TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE Dim_Time (
            time_key TEXT PRIMARY KEY,
            day INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            day_of_week TEXT NOT NULL,
            is_weekend BOOLEAN NOT NULL
        );
    """)

    # DDL: Central Fact Table
    cursor.execute("""
        CREATE TABLE Fact_Sales (
            sales_key INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            customer_key INTEGER NOT NULL,
            product_key INTEGER NOT NULL,
            store_key INTEGER NOT NULL,
            time_key TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_revenue REAL NOT NULL,
            total_profit REAL NOT NULL,
            FOREIGN KEY (customer_key) REFERENCES Dim_Customers (customer_key),
            FOREIGN KEY (product_key) REFERENCES Dim_Products (product_key),
            FOREIGN KEY (store_key) REFERENCES Dim_Stores (store_key),
            FOREIGN KEY (time_key) REFERENCES Dim_Time (time_key)
        );
    """)

    # Populate Gold Star Schema Tables
    print(" -> Loading Dim_Customers...")
    df_customers.to_sql("Dim_Customers", conn_dwh, if_exists="append", index=False)
    
    print(" -> Loading Dim_Products...")
    df_products.to_sql("Dim_Products", conn_dwh, if_exists="append", index=False)
    
    print(" -> Loading Dim_Stores...")
    df_stores.to_sql("Dim_Stores", conn_dwh, if_exists="append", index=False)

    print(" -> Loading Dim_Time...")
    df_time.to_sql("Dim_Time", conn_dwh, if_exists="append", index=False)

    print(" -> Loading Fact_Sales...")
    df_sales.to_sql("Fact_Sales", conn_dwh, if_exists="append", index=False)

    # -------------------------------------------------
    # UPGRADE: EXPLICIT B-TREE INDEXING ON FOREIGN KEYS
    # -------------------------------------------------
    print(" -> Creating high-performance Foreign Key B-Tree indexes on Fact_Sales...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON Fact_Sales(customer_key);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON Fact_Sales(product_key);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_sales_store ON Fact_Sales(store_key);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_sales_time ON Fact_Sales(time_key);")

    conn_dwh.commit()
    conn_dwh.close()

    print("\n==================================================")
    print(f"ETL PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Data Warehouse '{DWH_DATABASE}' is ready for analysis.")
    print("==================================================")

if __name__ == "__main__":
    run_etl()
