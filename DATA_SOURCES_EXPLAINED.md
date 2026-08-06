# 🌐 Data Sources & API Ingestion Architecture
## Smart Retail Data Warehouse

This document explains in detail how the **Smart Retail Data Warehouse** collects, cleans, and integrates multi-source data **without requiring any paid or private API keys**.

---

## ❓ Frequently Asked Question: "Why didn't I need an API Key?"

In production and data engineering hackathons, data is ingested from three primary types of public & open-access data endpoints:
1. **Public Open REST APIs**: Do not require authentication headers, bearer tokens, or API keys.
2. **Public Data Repositories**: Raw HTTP content hosted on GitHub or open data portals.
3. **Operational OLTP Relational Databases**: Seeded locally or hosted on cloud Postgres platforms (Supabase).

Below is the complete architectural breakdown of the 3 data sources used in this project.

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

* **Source Location**:
  * **Cloud Mode**: Supabase Cloud PostgreSQL (`postgresql://postgres:...@db.supabase.co:5432/postgres`)
  * **Local Fallback Mode**: `local_oltp.db` (Local Relational SQLite DB)
* **Format**: Relational SQL Database (`customers` & `stores` 3NF tables)
* **Authentication / API Key**: Managed via connection string or local database file.
* **Details**:
  * `setup_sources.py` automatically initializes and seeds 11 registered international customer profiles (`John Doe`, `Jane Smith`, `Arjun Mehta`, `Sophie Dubois`, `Yuki Tanaka`, etc.) across 6 countries (`United States`, `Canada`, `India`, `France`, `Germany`, `United Kingdom`) with loyalty tiers (`Gold`, `Silver`, `Bronze`).
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
