import sqlite3
import pandas as pd
from config import DWH_DATABASE

try:
    import streamlit as st
    cache_decorator = st.cache_data(ttl=300)
except ImportError:
    def cache_decorator(func):
        return func

def get_connection():
    """Returns a connection to the SQLite Data Warehouse."""
    return sqlite3.connect(DWH_DATABASE)

@cache_decorator
def query_sales_by_category():
    """Query 1: Sales Performance & Profitability by Product Category."""
    query = """
    SELECT 
        p.category AS 'Product Category', 
        COUNT(f.sales_key) AS 'Total Orders',
        SUM(f.quantity) AS 'Total Units Sold',
        ROUND(SUM(f.total_revenue), 2) AS 'Total Revenue ($)', 
        ROUND(SUM(f.total_profit), 2) AS 'Total Profit ($)',
        ROUND((SUM(f.total_profit) / SUM(f.total_revenue)) * 100, 2) AS 'Profit Margin (%)'
    FROM Fact_Sales f
    JOIN Dim_Products p ON f.product_key = p.product_key
    GROUP BY p.category
    ORDER BY SUM(f.total_revenue) DESC;
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

@cache_decorator
def query_top_customers(limit=5):
    """Query 2: Top Customers by Spend & Loyalty Tier."""
    query = f"""
    SELECT 
        c.customer_name AS 'Customer Name', 
        c.country AS 'Country', 
        c.membership_tier AS 'Loyalty Tier',
        COUNT(f.sales_key) AS 'Transaction Count',
        ROUND(SUM(f.total_revenue), 2) AS 'Total Spent ($)'
    FROM Fact_Sales f
    JOIN Dim_Customers c ON f.customer_key = c.customer_key
    GROUP BY c.customer_key
    ORDER BY SUM(f.total_revenue) DESC
    LIMIT {limit};
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

@cache_decorator
def query_monthly_sales_trend():
    """Query 3: Monthly Sales & Profit Trend."""
    query = """
    SELECT 
        t.year AS 'Year', 
        t.month AS 'Month', 
        ROUND(SUM(f.total_revenue), 2) AS 'Monthly Revenue ($)', 
        ROUND(SUM(f.total_profit), 2) AS 'Monthly Profit ($)',
        SUM(f.quantity) AS 'Quantity Sold'
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.time_key = t.time_key
    GROUP BY t.year, t.month
    ORDER BY t.year DESC, t.month DESC;
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

@cache_decorator
def query_revenue_by_country():
    """Query 4: Revenue & Orders by Country."""
    query = """
    SELECT 
        c.country AS 'Country', 
        COUNT(DISTINCT c.customer_key) AS 'Active Customers',
        COUNT(f.sales_key) AS 'Total Orders',
        ROUND(SUM(f.total_revenue), 2) AS 'Total Revenue ($)',
        ROUND(AVG(f.total_revenue), 2) AS 'Avg Order Value ($)'
    FROM Fact_Sales f
    JOIN Dim_Customers c ON f.customer_key = c.customer_key
    GROUP BY c.country
    ORDER BY SUM(f.total_revenue) DESC;
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

@cache_decorator
def query_low_stock_inventory():
    """Query 5: Simulated Stock & Inventory Reorder Alert."""
    query = """
    SELECT 
        p.product_key AS 'Product Key',
        p.product_name AS 'Product Name',
        p.category AS 'Category',
        p.unit_price AS 'Unit Price ($)',
        SUM(f.quantity) AS 'Historical Units Sold'
    FROM Dim_Products p
    LEFT JOIN Fact_Sales f ON p.product_key = f.product_key
    GROUP BY p.product_key
    ORDER BY SUM(f.quantity) DESC;
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

def run_all_analytical_queries():
    """Executes all analytical queries and prints formatting output to console."""
    print("==================================================")
    print("RUNNING ANALYTICAL QUERIES ON DATA WAREHOUSE")
    print("==================================================\n")

    print("--- Query 1: Sales Performance by Product Category ---")
    df1 = query_sales_by_category()
    print(df1.to_string(index=False))
    print("\n" + "-"*60 + "\n")

    print("--- Query 2: Top 5 Customers by Spend & Tier ---")
    df2 = query_top_customers(5)
    print(df2.to_string(index=False))
    print("\n" + "-"*60 + "\n")

    print("--- Query 3: Monthly Sales Trend (Recent Months) ---")
    df3 = query_monthly_sales_trend().head(10)
    print(df3.to_string(index=False))
    print("\n" + "-"*60 + "\n")

    print("--- Query 4: Revenue & Performance by Country ---")
    df4 = query_revenue_by_country()
    print(df4.to_string(index=False))
    print("\n" + "-"*60 + "\n")

    print("==================================================")
    print("ANALYSIS COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_all_analytical_queries()
