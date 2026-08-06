import sys
import os
import sqlite3
import unittest

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import DWH_DATABASE, LOCAL_OLTP_DATABASE
from setup_sources import setup_local_sqlite_oltp
from etl_pipeline import run_etl
from queries import query_sales_by_category, query_top_customers

class TestSmartRetailETL(unittest.TestCase):

    def test_01_setup_sources(self):
        """Test setting up local SQLite OLTP database."""
        setup_local_sqlite_oltp()
        self.assertTrue(os.path.exists(LOCAL_OLTP_DATABASE))
        
        conn = sqlite3.connect(LOCAL_OLTP_DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers;")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertGreater(count, 0)

    def test_02_etl_pipeline(self):
        """Test running complete Medallion ETL pipeline."""
        run_etl()
        self.assertTrue(os.path.exists(DWH_DATABASE))
        
        conn = sqlite3.connect(DWH_DATABASE)
        cursor = conn.cursor()
        
        # Check tables existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        required_tables = ["Dim_Customers", "Dim_Products", "Dim_Stores", "Dim_Time", "Fact_Sales"]
        for tbl in required_tables:
            self.assertIn(tbl, tables, f"Table '{tbl}' missing from Star Schema Data Warehouse!")
            
        cursor.execute("SELECT COUNT(*) FROM Fact_Sales;")
        fact_count = cursor.fetchone()[0]
        conn.close()
        self.assertGreater(fact_count, 0, "Fact_Sales table is empty!")

    def test_03_queries(self):
        """Test analytical SQL reporting queries."""
        df_cat = query_sales_by_category()
        self.assertFalse(df_cat.empty)
        self.assertIn("Total Revenue ($)", df_cat.columns)

        df_cust = query_top_customers(5)
        self.assertFalse(df_cust.empty)
        self.assertIn("Total Spent ($)", df_cust.columns)

if __name__ == "__main__":
    unittest.main()
