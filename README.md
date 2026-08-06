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
    subgraph Sources ["1. Data Sources (Raw Layer)"]
        S1["☁️ Supabase Cloud Postgres<br/>(Customers & Loyalty Profiles)"]
        S2["🌐 REST API Catalog<br/>(Live Inventory & Prices)"]
        S3["📁 GitHub CSV Repository<br/>(Historical Store Transactions)"]
    end

    subgraph ETL ["2. Python ETL Engine (Medallion Pipeline)"]
        B["🥉 Bronze Layer<br/>Raw JSON / CSV / SQL Dumps"]
        Si["🥈 Silver Layer<br/>Cleaned, Hash-Mapped, Deduplicated & Conformed Data"]
        G["🥇 Gold Layer<br/>Data Warehouse Star Schema Cube"]
        
        S1 --> B
        S2 --> B
        S3 --> B
        B -->|Extraction| Si
        Si -->|Conformed Joins & Facts| G
    end

    subgraph Target ["3. Data Warehouse (OLAP Target)"]
        DW[("🛢️ SQLite / DuckDB Data Warehouse<br/>(data_warehouse.db)")]
        G --> DW
    end

    subgraph Visual ["4. Presentation & BI Layer"]
        ST["📊 Streamlit Web Application<br/>(Real-Time Analytics Dashboard)"]
        AI["🤖 GenAI NL-to-SQL Assistant<br/>(Natural Language Query Agent)"]
        
        DW <--> ST
        DW <--> AI
        AI <--> ST
    end
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

## 🧪 5. Running Automated Tests

Verify pipeline transformation and schema integrity:
```bash
pytest tests/
```

---

## 👥 6. Hackathon Deliverables Checklist
- [x] Operational OLTP Database Schema (`setup_sources.py`)
- [x] Multi-Source Extraction & Medallion ETL Workflow (`etl_pipeline.py`)
- [x] Star Schema Analytical Data Warehouse (`data_warehouse.db`)
- [x] Interactive Streamlit Business Intelligence Dashboard (`app.py`)
- [x] Generative AI Natural Language to SQL Assistant (`genai_assistant.py`)
- [x] Unit Test Suite & Documentation (`tests/test_etl.py` & `README.md`)

---
