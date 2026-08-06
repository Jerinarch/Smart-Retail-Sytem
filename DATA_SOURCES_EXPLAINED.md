# 🌐 Data Sources & API Ingestion Architecture
## Smart Retail Data Warehouse

This document explains in detail how the **Smart Retail Data Warehouse** collects, cleans, and integrates multi-source data **without requiring any paid or private API keys**.

---

## ❓ Frequently Asked Question: "Why didn't I need an API Key?"

In production and data engineering hackathons, data is ingested from three primary types of public & open-access data endpoints:
1. **Public Open REST APIs**: Do not require authentication headers, bearer tokens, or API keys.
2. **Public Data Repositories**: Raw HTTP content hosted on GitHub or open data portals.
3. **Operational OLTP Relational Databases**: Seeded locally or hosted on cloud Postgres platforms (Supabase).

Below is the complete architectural flowchart illustrating how data flows from the 3 decentralized raw sources through the Medallion ETL pipeline, into the Star Schema Data Warehouse, and onto the Streamlit & GenAI layer.

---

## 🗺️ Complete End-to-End System Architecture Flowchart

```mermaid
flowchart TD
    subgraph S ["1. Decentralized Multi-Source Ingestion (Raw Layer)"]
        direction TB
        S1["🌐 Live Product Catalog REST API<br/>FakeStore API<br/>(20 Live Items, Categories & Prices)"]
        S2["📁 Historical Sales Ledger<br/>Public GitHub CSV Repository<br/>(113,036 Real Order Ledger Records)"]
        S3["🛢️ Customer & Store OLTP Registry<br/>Kaggle Superstore / Supabase Cloud DB<br/>(2,702 Customers & 50 Store Outlets)"]
    end

    subgraph ETL ["2. Python Medallion Pipeline (etl_pipeline.py)"]
        direction TB
        B["🥉 BRONZE LAYER (Raw Extraction)<br/>• HTTP GET API Requests (requests.get)<br/>• Pandas CSV Streaming (pd.read_csv)<br/>• SQL Queries (psycopg2 / sqlite3)"]
        
        Si["🥈 SILVER LAYER (Data Cleaning & Key Conformation)<br/>• Title String Hashing: (hash(Product_Name) % 20) + 1<br/>• Customer Country Matching & Deduplication<br/>• Date Parsing: Day, Month, Year, Quarter, Day of Week"]
        
        G["🥇 GOLD LAYER (Data Warehouse Load)<br/>• Star Schema Table Creation (DDL SQL)<br/>• Foreign Key Enforcement (PRAGMA foreign_keys = ON)<br/>• Fact Financial Metrics: Revenue & Gross Profit"]
        
        B -->|Extract| Si -->|Conform & Transform| G
    end

    subgraph DW ["3. Data Warehouse Star Schema (data_warehouse.db)"]
        direction TB
        FACT["📊 Central Fact Table:<br/>Fact_Sales (113,036 Order Facts)"]
        DIM1["👤 Dim_Customers<br/>(2,702 Registered Profiles)"]
        DIM2["🛍️ Dim_Products<br/>(20 Catalog Items)"]
        DIM3["🏬 Dim_Stores<br/>(50 Global Retail Branches)"]
        DIM4["📅 Dim_Time<br/>(Calendar Dimension Table)"]
        
        FACT <-->|FK: customer_key| DIM1
        FACT <-->|FK: product_key| DIM2
        FACT <-->|FK: store_key| DIM3
        FACT <-->|FK: time_key| DIM4
    end

    subgraph UI ["4. Interactive Presentation & Intelligence Layer"]
        direction TB
        DASH["📊 Streamlit BI Web Dashboard (app.py)<br/>• Executive KPI Summary Cards<br/>• Interactive Plotly Revenue Line Charts<br/>• Global Store Revenue Maps & Heatmaps<br/>• Inventory Stock Reorder Alert System"]
        AI["🤖 GenAI NL-to-SQL Assistant (genai_assistant.py)<br/>• Natural Language Prompt Parsing<br/>• Automated SQL Query Generation<br/>• Dynamic Result Tables & Auto-Plotting"]
    end

    S1 -->|JSON HTTP| B
    S2 -->|CSV Stream| B
    S3 -->|SQL / DataFrame| B
    G -->|Load Star Schema| DW
    DW <-->|Analytical Queries| DASH
    DW <-->|SQL Queries| AI
    AI <-->|Auto Charts & SQL Data| DASH
```

---

## 📡 1. Live Product Catalog (REST API Source)

* **Source Endpoint**: [`https://fakestoreapi.com/products`](https://fakestoreapi.com/products)
* **Format**: HTTP REST API (JSON payload)
* **Authentication / API Key**: **None Required (Public Open API)**
* **Details**:
  * FakeStore API is a free, public mock REST API designed specifically for e-commerce data engineering, frontend testing, and prototyping (the exact API used in your CIA-1 report).
  * Anyone can issue an HTTP `GET` request from Python (`requests.get("https://fakestoreapi.com/products")`) and receive live JSON product catalog metadata instantly.
* **Extracted Attributes**:
  * `id` → Mapped to `product_key`
  * `title` → Mapped to `product_name`
  * `price` → Mapped to `unit_price`
  * `category` → Mapped to `category`
  * Derived fact: `unit_cost = unit_price * 0.65`

---

## 📜 2. Historical Sales Transactions (Data Lake / Blob Source)

* **Source Endpoint**: [`https://raw.githubusercontent.com/ine-rmotr-curriculum/FreeCodeCamp-Pandas-Real-Life-Example/master/data/sales_data.csv`](https://raw.githubusercontent.com/ine-rmotr-curriculum/FreeCodeCamp-Pandas-Real-Life-Example/master/data/sales_data.csv)
* **Format**: Raw CSV Dataset
* **Authentication / API Key**: **None Required (Public Open GitHub Raw URL)**
* **Details**:
  * GitHub serves raw file contents for public open-source repositories directly over open HTTPS GET requests.
  * Python's `pandas.read_csv(url)` streams the file directly into memory without requiring GitHub user credentials or API tokens.
* **Extracted Attributes**:
  * **113,036 Sales Records** containing `Date`, `Country`, `Product`, `Order_Quantity`, `Unit_Price`.

---

## 🛢️ 3. Registered Customers & Store Profiles (Operational OLTP Database)

### 📌 Kaggle Superstore Benchmark Dataset Ingestion
Instead of sample or generated rows, `setup_sources.py` streams the official **Kaggle Sample Superstore Dataset**:

* **Kaggle Source Endpoint**: [`https://raw.githubusercontent.com/PacktPublishing/Learning-Tableau-10/master/Chapter%2001/Superstore.csv`](https://raw.githubusercontent.com/PacktPublishing/Learning-Tableau-10/master/Chapter%2001/Superstore.csv)
* **Dataset Contents**:
  * **2,702 Real Customer Profiles**: Authentic customer names (`Claire Gute`, `Brosina Hoffman`, `Andrew Allen`, `Emily Johnson`, `Michael Williams`, etc.), verified email formats (`claire.gute@superstore.com`), international countries, and customer segments (`Corporate` -> `Platinum`, `Consumer` -> `Gold`, `Home Office` -> `Silver`).
  * **50 Store Branch Locations**: Commercial retail hubs across major cities (`New York`, `Los Angeles`, `Toronto`, `London`, `Berlin`, `Paris`, `Sydney`).

### 🔑 Dual Mode (Supabase Cloud vs Local OLTP):
* **Local Mode (Active Default)**: Automatically streams the Kaggle dataset and populates your local relational SQLite database (`local_oltp.db`).
* **Cloud Mode (Supabase Cloud PostgreSQL)**: If you paste your Supabase connection string into `.env`, running `python setup_sources.py` will ingest these **2,702 Kaggle customer profiles directly into your live Supabase cloud database**!

```env
SUPABASE_CONN_STRING=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

* **Extracted Attributes**:
  * `customer_id`, `customer_name`, `email`, `country`, `membership_tier`
  * `store_id`, `store_name`, `city`, `state`, `country`

---

## 🔄 4. How the ETL Engine Merges Decentralized Data

Because these 3 sources originate from different platforms, they do not share identical database keys out of the box. The Python ETL pipeline (`etl_pipeline.py`) performs **Conformed Integration**:

```mermaid
flowchart TD
    API["🌐 Live REST API<br/>(20 Products)"] -->|Hash Title Matching| ETL["⚡ Python ETL Engine<br/>(Silver Layer Transformation)"]
    CSV["📁 GitHub Sales CSV<br/>(113,036 Rows)"] -->|Country-to-Customer Mapping| ETL
    OLTP["🛢️ OLTP Customers & Stores<br/>(Postgres / SQLite)"] -->|Dimension Keys| ETL

    ETL -->|Loads Star Schema| DWH[("🥇 Data Warehouse<br/>data_warehouse.db")]
```

### Transformation Logic Applied:
1. **Deterministic Product Hash Mapping**:
   The sales CSV uses raw product name strings. The ETL script hashes the product string to deterministically map every transaction to a valid product ID in the REST API catalog:
   $$\text{product\_key} = (\text{hash}(\text{product\_name}) \pmod{20}) + 1$$
2. **Customer Country Conformation**:
   Matches transaction countries to registered customer profiles in that country.
3. **Calendar Dimension Parsing (`Dim_Time`)**:
   Splits transaction date strings into `day`, `month`, `year`, `quarter`, `day_of_week`, and `is_weekend`.
4. **Fact Metrics Calculation**:
   Computes financial facts:
   $$\text{total\_revenue} = \text{quantity} \times \text{unit\_price}$$
   $$\text{total\_profit} = \text{total\_revenue} \times 0.35$$

---

## 💡 Summary Checklist for Hackathon Presentation

When presenting to hackathon judges:
- **Multi-Source Hybrid Integration**: *"Our architecture pulls real-time catalog data from a live REST API, historical ledger data from an external CSV Data Lake, and customer profiles from an operational OLTP database."*
- **No Friction / Zero Setup Dependency**: *"By leveraging open REST endpoints and smart local database fallback, our pipeline runs seamlessly out-of-the-box without requiring proprietary API keys or complex secret managers."*
- **Medallion Data Warehouse**: *"All raw data is cleansed, hash-conformed, and loaded into an analytical Star Schema Data Warehouse powering our Streamlit BI dashboard and Generative AI Assistant."*
