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
    page_title="Smart Retail Data Warehouse & AI Platform",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glassmorphism & Gradient Themes)
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 0.95rem;
        color: #a0aec0;
        margin-top: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .badge {
        background-color: #1A202C;
        color: #63B3ED;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #2B6CB0;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to check if DW exists
def check_dwh_exists():
    return os.path.exists(DWH_DATABASE)

# Sidebar Navigation
st.sidebar.title("🛒 Smart Retail DWH")
st.sidebar.markdown("<span class='badge'>Track 1 — Problem 1</span>", unsafe_allow_html=True)
st.sidebar.markdown("---")

navigation = st.sidebar.radio(
    "Navigation Menu",
    [
        "📊 Executive Dashboard",
        "🤖 GenAI SQL Assistant",
        "🗄️ Data Warehouse Explorer",
        "🔄 ETL Pipeline Control"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tech Stack**: Cloud Postgres (Supabase) + FakeStore REST API + GitHub CSV -> Medallion ETL -> Star Schema -> Streamlit BI & GenAI")

# Header Section
st.title("🛒 Smart Retail Data Warehouse & AI Analytics")
st.caption("Enterprise-grade Medallion Pipeline, Star Schema OLAP Cube, and Generative AI Assistant")

# Auto-trigger ETL if database does not exist
if not check_dwh_exists():
    st.warning("⚠️ Data Warehouse not found. Triggering initial ETL pipeline run...")
    with st.spinner("Extracting multi-source data and building Star Schema..."):
        run_etl()
    st.success("✅ Data Warehouse ready!")
    st.rerun()

# ---------------------------------------------------------
# PAGE 1: EXECUTIVE DASHBOARD
# ---------------------------------------------------------
if navigation == "📊 Executive Dashboard":
    df_cat = query_sales_by_category()
    df_cust = query_top_customers(10)
    df_trend = query_monthly_sales_trend()
    df_country = query_revenue_by_country()
    
    # Calculate Key Metrics
    total_rev = df_cat["Total Revenue ($)"].sum() if not df_cat.empty else 0
    total_profit = df_cat["Total Profit ($)"].sum() if not df_cat.empty else 0
    total_units = df_cat["Total Units Sold"].sum() if not df_cat.empty else 0
    avg_margin = (total_profit / total_rev * 100) if total_rev > 0 else 0

    # Metric Cards Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">${total_rev:,.2f}</div>
                <div class="metric-label">Total Sales Revenue</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">${total_profit:,.2f}</div>
                <div class="metric-label">Net Gross Profit</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_margin:.1f}%</div>
                <div class="metric-label">Avg Profit Margin</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_units:,}</div>
                <div class="metric-label">Total Units Sold</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row 1
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Revenue & Profit Monthly Trend")
        if not df_trend.empty:
            df_trend["Period"] = df_trend["Year"].astype(str) + "-" + df_trend["Month"].astype(str).str.zfill(2)
            fig_trend = px.line(
                df_trend.sort_values("Period"),
                x="Period",
                y=["Monthly Revenue ($)", "Monthly Profit ($)"],
                markers=True,
                color_discrete_sequence=["#00C9FF", "#92FE9D"],
                template="plotly_dark"
            )
            fig_trend.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.subheader("🛍️ Revenue by Product Category")
        if not df_cat.empty:
            fig_cat = px.bar(
                df_cat,
                x="Product Category",
                y="Total Revenue ($)",
                color="Profit Margin (%)",
                color_continuous_scale="Viridis",
                template="plotly_dark"
            )
            fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_cat, use_container_width=True)

    # Charts Row 2
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("🌍 Revenue Distribution by Country")
        if not df_country.empty:
            fig_geo = px.choropleth(
                df_country,
                locations="Country",
                locationmode="country names",
                color="Total Revenue ($)",
                hover_name="Country",
                color_continuous_scale="Blues",
                template="plotly_dark"
            )
            fig_geo.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_geo, use_container_width=True)

    with c4:
        st.subheader("👑 Top Customer Spenders")
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
# PAGE 2: GENAI SQL ASSISTANT
# ---------------------------------------------------------
elif navigation == "🤖 GenAI SQL Assistant":
    st.subheader("🤖 Natural Language to SQL Assistant")
    st.markdown("Ask any complex analytical question in plain English. The AI agent generates and runs SQL directly on the Data Warehouse.")

    sample_questions = [
        "Select a sample prompt or type your own below:",
        "Show sales performance by product category",
        "Who are the top customer spenders?",
        "Show monthly revenue trend",
        "Which countries generated the highest revenue?"
    ]
    
    selected_sample = st.selectbox("💡 Sample Prompts:", sample_questions)
    default_text = "" if selected_sample == sample_questions[0] else selected_sample
    
    user_prompt = st.text_input("💬 Ask your data question:", value=default_text, placeholder="e.g. Which category generated the highest profit margin?")

    if st.button("🚀 Execute AI Query", type="primary") and user_prompt:
        with st.spinner("Translating natural language to SQL and querying Data Warehouse..."):
            res = execute_nl_query(user_prompt)
        
        if res["success"]:
            st.success("✅ SQL Query Executed Successfully!")
            st.subheader("📝 Generated SQL Code")
            st.code(res["sql"], language="sql")
            
            st.subheader("📊 Query Output Results")
            df_out = res["data"]
            if not df_out.empty:
                st.dataframe(df_out, use_container_width=True, hide_index=True)
                
                # Auto Chart Rendering if numeric columns exist
                numeric_cols = df_out.select_dtypes(include=["number"]).columns.tolist()
                text_cols = df_out.select_dtypes(include=["object"]).columns.tolist()
                
                if text_cols and numeric_cols:
                    st.subheader("📈 Dynamic Visualization")
                    fig_auto = px.bar(
                        df_out,
                        x=text_cols[0],
                        y=numeric_cols[0],
                        color=numeric_cols[0],
                        color_continuous_scale="Plasma",
                        template="plotly_dark"
                    )
                    fig_auto.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_auto, use_container_width=True)
            else:
                st.info("Query returned no matching records.")
        else:
            st.error(f"❌ SQL Execution Error: {res['error']}")

# ---------------------------------------------------------
# PAGE 3: DATA WAREHOUSE EXPLORER
# ---------------------------------------------------------
elif navigation == "🗄️ Data Warehouse Explorer":
    st.subheader("🗄️ Data Warehouse Star Schema Explorer")
    
    conn = sqlite3.connect(DWH_DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if t[0] != "sqlite_sequence"]
    
    selected_table = st.selectbox("Select Star Schema Table to Inspect:", tables)
    
    if selected_table:
        df_tbl = pd.read_sql_query(f"SELECT * FROM {selected_table} LIMIT 100", conn)
        st.markdown(f"**Table Preview (`{selected_table}` - Top 100 rows):**")
        st.dataframe(df_tbl, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("⚡ Custom SQL Query Sandbox")
    custom_sql = st.text_area("Write SQL Query:", value="SELECT * FROM Fact_Sales f JOIN Dim_Products p ON f.product_key = p.product_key LIMIT 10;")
    if st.button("Run SQL"):
        try:
            df_custom = pd.read_sql_query(custom_sql, conn)
            st.dataframe(df_custom, use_container_width=True)
        except Exception as e:
            st.error(f"Error executing query: {e}")
    conn.close()

# ---------------------------------------------------------
# PAGE 4: ETL PIPELINE CONTROL
# ---------------------------------------------------------
elif navigation == "🔄 ETL Pipeline Control":
    st.subheader("🔄 Medallion ETL Pipeline Control Center")
    st.markdown("Re-run the extraction, cleaning, key conformation, and Star Schema loading on demand.")
    
    if st.button("▶️ Run Complete ETL Pipeline", type="primary"):
        with st.spinner("Running Medallion ETL Engine..."):
            run_etl()
        st.success("✅ ETL Pipeline completed! Star Schema refreshed.")
        st.balloons()
