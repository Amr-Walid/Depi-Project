"""
Centralized configuration for CryptoPulse Backend.
Reads from environment variables with sensible defaults for local development.
"""
import os
from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────
# PostgreSQL Database
# ──────────────────────────────────────────────
from urllib.parse import quote_plus

POSTGRES_USER = os.getenv("POSTGRES_USER") or "postgres"
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD") or ""
POSTGRES_HOST = os.getenv("POSTGRES_HOST") or "localhost"
POSTGRES_PORT = os.getenv("POSTGRES_PORT") or "5432"
POSTGRES_DB = os.getenv("POSTGRES_DB") or "postgres"

# Encode password to handle special characters like '@'
encoded_password = quote_plus(POSTGRES_PASSWORD)

DATABASE_URL = os.getenv("DATABASE_URL") or f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode=require"

# ──────────────────────────────────────────────
# JWT Authentication
# ──────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "crypto-pulse-dev-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ──────────────────────────────────────────────
# Azure Data Lake (for future ADLS integration)
# ──────────────────────────────────────────────
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "")

# ──────────────────────────────────────────────
# Supported Coins (from historical_fetcher.py)
# ──────────────────────────────────────────────
SUPPORTED_COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "DOTUSDT", "DOGEUSDT", "MATICUSDT", "LINKUSDT",
    "AVAXUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
    "XLMUSDT", "ALGOUSDT", "VETUSDT", "ICPUSDT", "FILUSDT",
]
