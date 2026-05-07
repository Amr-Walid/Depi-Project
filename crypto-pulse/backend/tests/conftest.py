"""
Test configuration — fixtures for all API tests.

Uses SQLite in-memory database for test isolation.
No Docker required to run tests.
"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import SUPPORTED_COINS
from app.database import Base, get_db
from app.main import app

# ──────────────────────────────────────────────
# SQLite in-memory database for tests
# ──────────────────────────────────────────────
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_gold_daily_market_summary():
    """Attach and seed the Gold market table needed by coin endpoint tests."""
    with engine.begin() as conn:
        attached_databases = conn.execute(text("PRAGMA database_list")).fetchall()
        if not any(row[1] == "gold" for row in attached_databases):
            conn.execute(text("ATTACH DATABASE ':memory:' AS gold"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold.daily_market_summary (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                total_volume REAL NOT NULL
            )
        """))
        conn.execute(text("DELETE FROM gold.daily_market_summary"))

        start_date = date(2026, 5, 1) - timedelta(days=29)
        rows = []
        for day_offset in range(30):
            trading_date = start_date + timedelta(days=day_offset)
            for coin_index, symbol in enumerate(SUPPORTED_COINS):
                base_price = 100.0 + (coin_index * 25.0)
                open_price = base_price + day_offset
                change_pct = (coin_index - 10) / 100.0
                close_price = open_price * (1 + change_pct)
                rows.append({
                    "symbol": symbol,
                    "date": trading_date.strftime("%Y-%m-%d"),
                    "open_price": open_price,
                    "high_price": max(open_price, close_price) * 1.01,
                    "low_price": min(open_price, close_price) * 0.99,
                    "close_price": close_price,
                    "total_volume": 10000.0 + (coin_index * 100.0) + day_offset,
                })

        conn.execute(text("""
            INSERT INTO gold.daily_market_summary (
                symbol, date, open_price, high_price, low_price, close_price, total_volume
            ) VALUES (
                :symbol, :date, :open_price, :high_price, :low_price, :close_price, :total_volume
            )
        """), rows)


def override_get_db():
    """Override the get_db dependency to use the test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────
@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    seed_gold_daily_market_summary()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Provides a TestClient instance for making API requests."""
    return TestClient(app)


@pytest.fixture
def test_user(client):
    """
    Creates a test user and returns user info + tokens.
    
    Returns:
        dict with keys: email, password, access_token, refresh_token, user_id
    """
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 201
    tokens = response.json()
    return {
        "email": user_data["email"],
        "password": user_data["password"],
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


@pytest.fixture
def auth_headers(test_user):
    """Returns authorization headers with a valid Bearer token."""
    return {"Authorization": f"Bearer {test_user['access_token']}"}
