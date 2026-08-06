import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os

from config import DWH_DATABASE
from queries import (
    query_sales_by_category,
    query_top_customers,
    query_monthly_sales_trend,
    query_revenue_by_country,
    query_low_stock_inventory
)
from etl_pipeline import run_etl
from genai_assistant import execute_nl_query

# Page Configuration
st.set_page_config(
    page_title="Smart Retail Data Warehouse Platform",
    page_icon="🏬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise Design System (Charcoal & Amber/Emerald Premium Theme)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Header Styling */
    .app-title {
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #ffffff;
        margin-bottom: 0.2rem;
    }
    
    .app-subtitle {
        font-size: 1.0rem;
        color: #94a3b8;
        margin-bottom: 1.8rem;
        font-weight: 400;
    }
    
    /* Premium Metric Card System */
    .metric-container {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-container:hover {
        border-color: #f59e0b;
        transform: translateY(-1px);
    }
    
    .metric-label {
        font-size: 0.825rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
    }
    
    .metric-accent-emerald {
        color: #10b981;
    }
    
    .metric-accent-amber {
        color: #f59e0b;
    }
    
    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: #0b1329;
        border-right: 1px solid #1e293b;
    }
    
    /* Table & Container Styling */
    .stDataFrame {
        border: 1px solid #334155;
        border-radius: 6px;
    }
    
    /* Custom Badge */
    .status-badge {
        display: inline-block;
        background-color: #1e293b;
        color: #f59e0b;
        border: 1px solid #d97706;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to verify Data Warehouse existence
def check_dwh_exists():
    return os.path.exists(DWH_DATABASE)

# Sidebar Navigation
st.sidebar.markdown("<h2 style='font-size:1.3rem; font-weight:700; color:#ffffff; margin-bottom:20px;'>Smart Retail DWH</h2>", unsafe_allow_html=True)

navigation = st.sidebar.radio(
    "Select Interface View",
    [
        "Executive Dashboard",
        "Natural Language Assistant",
        "Data Warehouse Explorer",
        "ETL Control Center"
    ]
)

# Header Bar
st.markdown("<div class='app-title'>Smart Retail Data Warehouse Platform</div>", unsafe_allow_html=True)
st.markdown("<div class='app-subtitle'>Enterprise Analytics, Dimensional Star Schema Modeling, and SQL Data Intelligence</div>", unsafe_allow_html=True)

# Auto-initialize Data Warehouse if missing
if not check_dwh_exists():
    st.warning("Data Warehouse instance not detected. Initializing setup and Medallion ETL pipeline...")
    with st.spinner("Extracting datasets and generating Star Schema..."):
        run_etl()
        st.cache_data.clear()
    st.success("Data Warehouse successfully loaded.")
    st.rerun()

# ---------------------------------------------------------
# VIEW 1: EXECUTIVE DASHBOARD
# ---------------------------------------------------------
if navigation == "Executive Dashboard":
    df_cat = query_sales_by_category()
    df_cust = query_top_customers(10)
    df_trend = query_monthly_sales_trend()
    df_country = query_revenue_by_country()
    
    # Financial Fact Calculations
    total_rev = df_cat["Total Revenue ($)"].sum() if not df_cat.empty else 0
    total_profit = df_cat["Total Profit ($)"].sum() if not df_cat.empty else 0
    total_units = df_cat["Total Units Sold"].sum() if not df_cat.empty else 0
    avg_margin = (total_profit / total_rev * 100) if total_rev > 0 else 0

    # Executive Key Performance Indicators
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Total Revenue</div>
                <div class="metric-value">${total_rev:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Gross Net Profit</div>
                <div class="metric-value metric-accent-emerald">${total_profit:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Average Profit Margin</div>
                <div class="metric-value metric-accent-amber">{avg_margin:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Total Units Sold</div>
                <div class="metric-value">{total_units:,}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visualization Row 1
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Financial Performance Trend (Monthly)")
        if not df_trend.empty:
            df_trend["Period"] = df_trend["Year"].astype(str) + "-" + df_trend["Month"].astype(str).str.zfill(2)
            fig_trend = px.line(
                df_trend.sort_values("Period"),
                x="Period",
                y=["Monthly Revenue ($)", "Monthly Profit ($)"],
                markers=True,
                color_discrete_sequence=["#f59e0b", "#10b981"],
                template="plotly_dark"
            )
            fig_trend.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.markdown("#### Revenue Performance by Product Category")
        if not df_cat.empty:
            fig_cat = px.bar(
                df_cat,
                x="Product Category",
                y="Total Revenue ($)",
                color="Profit Margin (%)",
                color_continuous_scale="Cividis",
                template="plotly_dark"
            )
            fig_cat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_cat, use_container_width=True)

    # Visualization Row 2
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Geographic Revenue Distribution")
        if not df_country.empty:
            fig_geo = px.choropleth(
                df_country,
                locations="Country",
                locationmode="country names",
                color="Total Revenue ($)",
                hover_name="Country",
                color_continuous_scale="Purples",
                template="plotly_dark"
            )
            fig_geo.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig_geo, use_container_width=True)

    with c4:
        st.markdown("#### Top Customer Spenders")
        if not df_cust.empty:
            st.dataframe(
                df_cust,
                column_config={
                    "Total Spent ($)": st.column_config.NumberColumn(format="$%.2f")
                },
                use_container_width=True,
                hide_index=True
            )

# ---------------------------------------------------------
# VIEW 2: NATURAL LANGUAGE ASSISTANT
# ---------------------------------------------------------
elif navigation == "Natural Language Assistant":
    st.markdown("#### Natural Language to SQL Query Interface")
    st.markdown("Enter analytical questions in standard English. The query engine generates, validates, and executes read-only SQL against the Data Warehouse.")

    sample_questions = [
        "Select a pre-configured query prompt or type a custom question below:",
        "Show sales performance by product category",
        "Who are the top customer spenders?",
        "Show monthly revenue trend",
        "Which countries generated the highest revenue?"
    ]
    
    selected_sample = st.selectbox("Pre-configured Prompts:", sample_questions)
    default_text = "" if selected_sample == sample_questions[0] else selected_sample
    
    user_prompt = st.text_input("Analytical Query Prompt:", value=default_text, placeholder="e.g., Which product category yielded the highest profit margin?")

    if st.button("Execute Query", type="primary") and user_prompt:
        with st.spinner("Processing natural language translation and validating SQL security..."):
            res = execute_nl_query(user_prompt)
        
        if res["success"]:
            st.success("Query Executed Successfully")
            st.markdown("##### Executed SQL Code")
            st.code(res["sql"], language="sql")
            
            st.markdown("##### Query Result Dataset")
            df_out = res["data"]
            if not df_out.empty:
                st.dataframe(df_out, use_container_width=True, hide_index=True)
                
                # Dynamic Visualization for numeric results
                numeric_cols = df_out.select_dtypes(include=["number"]).columns.tolist()
                text_cols = df_out.select_dtypes(include=["object"]).columns.tolist()
                
                if text_cols and numeric_cols:
                    st.markdown("##### Data Chart Visualization")
                    fig_auto = px.bar(
                        df_out,
                        x=text_cols[0],
                        y=numeric_cols[0],
                        color=numeric_cols[0],
                        color_continuous_scale="Amber",
                        template="plotly_dark"
                    )
                    fig_auto.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_auto, use_container_width=True)
            else:
                st.info("The executed query returned zero records.")
        else:
            st.error(f"Execution Error: {res['error']}")

# ---------------------------------------------------------
# VIEW 3: DATA WAREHOUSE EXPLORER
# ---------------------------------------------------------
elif navigation == "Data Warehouse Explorer":
    st.markdown("#### Star Schema Data Warehouse Inspection")
    
    conn = sqlite3.connect(DWH_DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if t[0] != "sqlite_sequence"]
    
    selected_table = st.selectbox("Select Star Schema Table:", tables)
    
    if selected_table:
        df_tbl = pd.read_sql_query(f"SELECT * FROM {selected_table} LIMIT 100", conn)
        st.markdown(f"**Table Records Preview (`{selected_table}` - Top 100 rows):**")
        st.dataframe(df_tbl, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### Custom SQL Execution Sandbox")
    st.markdown("Read-only SQL sandbox enforced by security guardrails.")
    
    custom_sql = st.text_area("SQL Query Input:", value="SELECT * FROM Fact_Sales f JOIN Dim_Products p ON f.product_key = p.product_key LIMIT 10;")
    if st.button("Run Sandbox SQL"):
        from genai_assistant import is_safe_sql
        is_safe, err_msg = is_safe_sql(custom_sql)
        if not is_safe:
            st.error(f"Security Policy Violation: {err_msg}")
        else:
            try:
                df_custom = pd.read_sql_query(custom_sql, conn)
                st.dataframe(df_custom, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Syntax Error: {e}")
    conn.close()

# ---------------------------------------------------------
# VIEW 4: ETL CONTROL CENTER
# ---------------------------------------------------------
elif navigation == "ETL Control Center":
    st.markdown("#### Medallion ETL Pipeline Control Center")
    st.markdown("Trigger full extraction from public endpoints, transform conformed dimension keys, and refresh the Star Schema Data Warehouse.")
    
    if st.button("Run ETL Pipeline Refresh", type="primary"):
        with st.spinner("Executing extraction, key transformation, and data warehouse loading..."):
            run_etl()
            st.cache_data.clear()
        st.success("ETL Pipeline Execution Complete. Data Warehouse successfully updated.")
