import os
import sqlite3
import re
import pandas as pd
from config import DWH_DATABASE, OPENAI_API_KEY, GROQ_API_KEY

SCHEMA_PROMPT_CONTEXT = """
Database Schema (SQLite Data Warehouse Star Schema):
1. Dim_Customers (customer_key INTEGER PK, customer_name TEXT, email TEXT, country TEXT, membership_tier TEXT)
2. Dim_Products (product_key INTEGER PK, product_name TEXT, category TEXT, unit_price REAL, unit_cost REAL)
3. Dim_Stores (store_key INTEGER PK, store_name TEXT, city TEXT, state TEXT, country TEXT)
4. Dim_Time (time_key TEXT PK, day INTEGER, month INTEGER, year INTEGER, quarter INTEGER, day_of_week TEXT, is_weekend BOOLEAN)
5. Fact_Sales (sales_key INTEGER PK, transaction_id TEXT, customer_key FK, product_key FK, store_key FK, time_key FK, quantity INTEGER, unit_price REAL, total_revenue REAL, total_profit REAL)
"""

FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE", "CREATE", "GRANT", "PRAGMA"]

def is_safe_sql(sql_query: str) -> tuple[bool, str]:
    """Inspects SQL query to ensure it is strictly a READ-ONLY SELECT query."""
    upper_sql = sql_query.upper().strip()
    
    # Check for forbidden destructive keywords
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(r"\b" + kw + r"\b", upper_sql):
            return False, f"Destructive SQL Operation Blocked: Contains forbidden keyword '{kw}'."
            
    if not upper_sql.startswith("SELECT") and not upper_sql.startswith("WITH"):
        return False, "Security Guardrail Blocked: Only SELECT or WITH read-only queries are permitted."
        
    return True, ""

def generate_sql_heuristic(nl_prompt: str) -> str:
    """Fallback keyword-based natural language to SQL translator."""
    prompt_lower = nl_prompt.lower()
    
    if "category" in prompt_lower or "categories" in prompt_lower:
        return """
        SELECT p.category AS Category, ROUND(SUM(f.total_revenue), 2) AS Revenue, SUM(f.quantity) AS Quantity_Sold
        FROM Fact_Sales f JOIN Dim_Products p ON f.product_key = p.product_key
        GROUP BY p.category ORDER BY Revenue DESC;
        """
    elif "customer" in prompt_lower or "spend" in prompt_lower or "top spender" in prompt_lower:
        return """
        SELECT c.customer_name AS Customer, c.country AS Country, c.membership_tier AS Tier, ROUND(SUM(f.total_revenue), 2) AS Total_Spent
        FROM Fact_Sales f JOIN Dim_Customers c ON f.customer_key = c.customer_key
        GROUP BY c.customer_key ORDER BY Total_Spent DESC LIMIT 10;
        """
    elif "country" in prompt_lower or "region" in prompt_lower or "location" in prompt_lower:
        return """
        SELECT c.country AS Country, COUNT(f.sales_key) AS Orders, ROUND(SUM(f.total_revenue), 2) AS Revenue
        FROM Fact_Sales f JOIN Dim_Customers c ON f.customer_key = c.customer_key
        GROUP BY c.country ORDER BY Revenue DESC;
        """
    elif "month" in prompt_lower or "year" in prompt_lower or "trend" in prompt_lower:
        return """
        SELECT t.year AS Year, t.month AS Month, ROUND(SUM(f.total_revenue), 2) AS Revenue, ROUND(SUM(f.total_profit), 2) AS Profit
        FROM Fact_Sales f JOIN Dim_Time t ON f.time_key = t.time_key
        GROUP BY t.year, t.month ORDER BY Year DESC, Month DESC LIMIT 12;
        """
    elif "profit" in prompt_lower or "margin" in prompt_lower:
        return """
        SELECT p.category AS Category, ROUND(SUM(f.total_revenue), 2) AS Revenue, ROUND(SUM(f.total_profit), 2) AS Profit
        FROM Fact_Sales f JOIN Dim_Products p ON f.product_key = p.product_key
        GROUP BY p.category ORDER BY Profit DESC;
        """
    else:
        return """
        SELECT f.transaction_id, c.customer_name, p.product_name, p.category, f.total_revenue
        FROM Fact_Sales f
        JOIN Dim_Customers c ON f.customer_key = c.customer_key
        JOIN Dim_Products p ON f.product_key = p.product_key
        LIMIT 10;
        """

def generate_sql_with_llm(nl_prompt: str) -> str:
    """Converts natural language into SQL query using OpenAI API if configured."""
    if not OPENAI_API_KEY:
        return generate_sql_heuristic(nl_prompt)
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        system_instruction = (
            "You are a expert SQL Data Engineer. Translate the user's natural language question into a valid SQLite SQL query.\n"
            f"{SCHEMA_PROMPT_CONTEXT}\n"
            "Return ONLY the executable SQL query inside a markdown code block ```sql ... ``` without additional chatter."
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": nl_prompt}
            ],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        match = re.search(r"```sql\s*(.*?)\s*```", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content
    except Exception as e:
        print(f"[WARNING] OpenAI API call failed ({e}). Falling back to heuristic NL-to-SQL...")
        return generate_sql_heuristic(nl_prompt)

def execute_nl_query(nl_prompt: str):
    """Parses NL prompt, converts to SQL, validates read-only security, and executes query."""
    sql_query = generate_sql_with_llm(nl_prompt)
    sql_clean = re.sub(r"```sql|```", "", sql_query).strip()
    
    # Security Validation Guardrail
    is_safe, error_msg = is_safe_sql(sql_clean)
    if not is_safe:
        return {
            "success": False,
            "sql": sql_clean,
            "data": pd.DataFrame(),
            "error": error_msg
        }
        
    try:
        conn = sqlite3.connect(DWH_DATABASE)
        df_result = pd.read_sql_query(sql_clean, conn)
        conn.close()
        return {
            "success": True,
            "sql": sql_clean,
            "data": df_result,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "sql": sql_clean,
            "data": pd.DataFrame(),
            "error": str(e)
        }

if __name__ == "__main__":
    prompt = "Show top revenue by product category"
    print(f"Testing NL Query: '{prompt}'")
    res = execute_nl_query(prompt)
    print("Generated SQL:\n", res["sql"])
    print("\nResult Data:\n", res["data"])
