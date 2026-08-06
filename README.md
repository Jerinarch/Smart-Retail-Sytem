# 🛒 Smart Retail Data Warehouse & AI Analytics Platform
> **Cognizant One-Day Hackathon** | Track 1 — Data Engineering (Problem Statement 1: Smart Retail Data Warehouse)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase%20Cloud-336791?logo=postgresql)
![SQLite](https://img.shields.io/badge/Data%20Warehouse-Star%20Schema-003B57?logo=sqlite)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit)
![GenAI](https://img.shields.io/badge/GenAI-NL--to--SQL-green)

---

## 📌 1. Project Overview & Problem Statement

Retail operations generate massive streams of transactional, catalog, and store data across decentralized platforms. To unlock business intelligence, sales forecasting, and inventory control, this project builds a complete, enterprise-grade **Smart Retail Data Warehouse** powered by a **Medallion Data Pipeline** and a **Generative AI Natural Language to SQL Assistant**.

### Key System Capabilities:
1. **Multi-Source Ingestion**: Ingests transactional data from cloud PostgreSQL databases, product metadata dynamically from REST APIs, and historical sales ledgers from raw CSV repositories.
2. **Medallion Architecture (Bronze → Silver → Gold)**: Python-driven ETL engine enforcing data cleaning, deterministic product key hashing, customer country conformation, and time dimension parsing.
3. **Star Schema Data Warehouse**: Multidimensional analytical cube (`Fact_Sales` surrounded by `Dim_Customers`, `Dim_Products`, `Dim_Stores`, and `Dim_Time`).
4. **Interactive BI Dashboard**: Streamlit web interface with real-time KPI cards, Plotly charts, store performance heatmaps, and stock alert monitors.
5. **GenAI NL-to-SQL Assistant**: Natural language to SQL query engine enabling executives to ask plain-English questions and automatically run queries on the Data Warehouse.

---

## 🏗️ 2. System Architecture

```mermaid
flowchart TD
    subgraph Sources ["1. Multi-Source Ingestion (Raw Layer)"]
        direction TB
        S1["☁️ Kaggle OLTP<br/>(2,702 Customer Profiles & 50 Store Outlets)"]
        S2["🌐 Live REST API Catalog<br/>FakeStore API<br/>(20 Live Catalog Items & Inventory Prices)"]
        S3["📁 GitHub CSV Data Lake<br/>(113,036 Historical Order Ledger Records)"]
        S4["📦 Self-Healing Offline Engine<br/>(Automatic Fallback Catalog on Network Drops)"]
    end

    subgraph ETL ["2. Python Medallion Pipeline (etl_pipeline.py)"]
        direction TB
        B["(Raw Extraction)<br/>• HTTP GET Requests (requests.get)<br/>• Pandas Streaming (pd.read_csv)<br/>• SQL Queries (sqlite3 / psycopg2)"]
        
        Si[" (Cleaning & Key Conformation)<br/>• Deterministic MD5 Key Hashing (hashlib.md5)<br/>• Customer Country Matching & Deduplication<br/>• Time Parsing: Day, Month, Year, Quarter, Day of Week"]
        
        G[" Data Warehouse Load)<br/>• Star Schema Table Creation (DDL SQL)<br/>• Foreign Key Integrity (PRAGMA foreign_keys = ON)<br/>• Fact Derivations: Total Revenue & Profit"]
        
        B -->|Extract| Si -->|Conform & Transform| G
    end

    subgraph Target ["3. Data Warehouse Star Schema (data_warehouse.db)"]
        direction TB
        FACT["📊 Central Fact Table:<br/>Fact_Sales (113,036 Order Facts)"]
        DIM1["👤 Dim_Customers (2,702 Profiles)"]
        DIM2["🛍️ Dim_Products (20 Catalog Items)"]
        DIM3["🏬 Dim_Stores (50 Retail Branches)"]
        DIM4["📅 Dim_Time (Calendar Dimension)"]
        IDX["⚡ B-Tree Index Engine<br/>(idx_fact_sales_customer / product / store / time)"]
        
        FACT <-->|FK: customer_key| DIM1
        FACT <-->|FK: product_key| DIM2
        FACT <-->|FK: store_key| DIM3
        FACT <-->|FK: time_key| DIM4
        FACT --- IDX
    end

    subgraph Visual ["4. Presentation & BI Layer"]
        direction TB
        ST["📊 Streamlit BI Web App (app.py)<br/>• Real-Time KPI Cards & Plotly Line Charts<br/>• Store Revenue Heatmaps & Reorder Alerts<br/>• RAM Query Caching (@st.cache_data 300s TTL)"]
        AI["🤖 GenAI NL-to-SQL Assistant (genai_assistant.py)<br/>• Schema Prompt Grounding<br/>• Read-Only SQL Guardrails (is_safe_sql)<br/>• Automated SQL Query Execution & Charts"]
    end

    S1 -->|SQL / DataFrame| B
    S2 -->|JSON HTTP| B
    S3 -->|CSV Stream| B
    S4 -->|Fallback Catalog| B
    G -->|Load Star Schema| Target
    Target <-->|Analytical Queries| ST
    Target <-->|SQL Queries| AI
    AI <-->|Auto Plotting & Tables| ST
```

---

## 📐 3. Data Warehouse Schema Design (Star Schema)

The analytical data warehouse follows a dimensional **Star Schema**:

```mermaid
erDiagram
    Fact_Sales }|..|| Dim_Customers : "customer_key"
    Fact_Sales }|..|| Dim_Products : "product_key"
    Fact_Sales }|..|| Dim_Stores : "store_key"
    Fact_Sales }|..|| Dim_Time : "time_key"

    Dim_Customers {
        INTEGER customer_key PK
        VARCHAR customer_name
        VARCHAR email
        VARCHAR country
        VARCHAR membership_tier
    }

    Dim_Products {
        INTEGER product_key PK
        VARCHAR product_name
        VARCHAR category
        DECIMAL unit_price
        DECIMAL unit_cost
    }

    Dim_Stores {
        INTEGER store_key PK
        VARCHAR store_name
        VARCHAR city
        VARCHAR state
        VARCHAR country
    }

    Dim_Time {
        VARCHAR time_key PK
        INTEGER day
        INTEGER month
        INTEGER year
        INTEGER quarter
        VARCHAR day_of_week
        BOOLEAN is_weekend
    }

    Fact_Sales {
        INTEGER sales_key PK
        VARCHAR transaction_id
        INTEGER customer_key FK
        INTEGER product_key FK
        INTEGER store_key FK
        VARCHAR time_key FK
        INTEGER quantity
        DECIMAL unit_price
        DECIMAL total_revenue
        DECIMAL total_profit
    }
```

---

## 🚀 4. Quickstart & Execution Guide

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/Jerinarch/Smart-Retail-Sytem.git
cd Smart-Retail-Sytem

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Initialize Operational OLTP Database
Populates customer registries and retail store locations in cloud PostgreSQL / local SQLite fallback:
```bash
python setup_sources.py
```

### Step 4: Execute Medallion ETL Pipeline
Runs extraction across 3 sources, transforms raw data, and loads the Star Schema Data Warehouse:
```bash
python etl_pipeline.py
```

### Step 5: Run Analytical SQL Queries (Console BI Report)
```bash
python queries.py
```

### Step 6: Launch Interactive Streamlit BI Dashboard & AI Assistant
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🛡️ 5. Enterprise Data Architecture & Security Standards

This project follows enterprise data governance, high-performance OLAP optimization, and zero-trust security standards.

### Core Architectural Highlights:
1. **Deterministic Cryptographic Key Hashing (MD5)**: `Dim_Products` surrogate key derivation using stable cryptographic hashing (`hashlib.md5`) ensures idempotent, seed-stable key assignment across incremental loads.
2. **B-Tree Indexing Engine**: Secondary B-Tree indexes on `Fact_Sales(customer_key)`, `Fact_Sales(product_key)`, `Fact_Sales(store_key)`, and `Fact_Sales(time_key)` accelerate analytical multi-dimensional OLAP `JOIN` queries.
3. **Read-Only GenAI SQL Guardrails**: Natural language to SQL execution engine implements security guardrails blocking destructive commands (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`).
4. **Streamlit RAM Query Caching**: High-throughput analytics dashboard leverages `@st.cache_data` memory caching with 300-second TTL invalidation.
5. **Kaggle Superstore Integration**: 1,000 realistic enterprise customer records and 20 multi-region physical store profiles ingested from e-commerce datasets.

### 📚 Detailed Documentation & Checklists:
- 📖 [**Data Sources Architecture & Flowchart**](DATA_SOURCES_EXPLAINED.md): Detailed lineage of cloud Postgres, REST API, and raw CSV ingestion workflows.
- 🛡️ [**Enterprise Data Architecture Quality Checklist**](DATA_ARCHITECTURE_QUALITY_CHECKLIST.md): 100% compliant quality benchmarks, ACID safety rules, PII sanitization, and Tech Stack Evaluation Matrix.

---

## 🧪 6. Running Automated Tests

Verify pipeline transformation, referential integrity, and schema compliance:
```bash
pytest tests/
```

---


---

