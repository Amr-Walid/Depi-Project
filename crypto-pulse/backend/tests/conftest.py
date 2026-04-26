"""
Test configuration — fixtures for all API tests.

Uses SQLite in-memory database for test isolation.
No Docker required to run tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
