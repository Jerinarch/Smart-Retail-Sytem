import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Data Warehouse & Local OLTP Database Paths
DWH_DATABASE = os.getenv("DWH_DATABASE", "data_warehouse.db")
LOCAL_OLTP_DATABASE = os.getenv("LOCAL_OLTP_DATABASE", "local_oltp.db")

# Cloud Supabase Connection String (Default placeholder if not configured)
SUPABASE_CONN_STRING = os.getenv(
    "SUPABASE_CONN_STRING",
    "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
)

# External Data Source Endpoints
FAKESTORE_API_URL = "https://fakestoreapi.com/products"
DUMMYJSON_API_URL = "https://dummyjson.com/products?limit=100"
GITHUB_SALES_CSV_URL = (
    "https://raw.githubusercontent.com/ine-rmotr-curriculum/"
    "FreeCodeCamp-Pandas-Real-Life-Example/master/data/sales_data.csv"
)

# Generative AI Credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def is_supabase_configured() -> bool:
    """Checks if a valid Supabase connection string is provided in environment."""
    return (
        SUPABASE_CONN_STRING is not None
        and "[YOUR-PASSWORD]" not in SUPABASE_CONN_STRING
        and "[YOUR-PROJECT-REF]" not in SUPABASE_CONN_STRING
        and len(SUPABASE_CONN_STRING.strip()) > 0
    )
