"""
Database engine, session factory, and FastAPI dependency.
Uses SQLAlchemy 2.0 style with synchronous sessions.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# ──────────────────────────────────────────────
# SQLAlchemy Engine & Session
# ──────────────────────────────────────────────
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


# ──────────────────────────────────────────────
# FastAPI Dependency — yields a DB session per request
# ──────────────────────────────────────────────
def get_db():
    """
    Dependency that provides a SQLAlchemy session.
    Automatically closes the session after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables defined by ORM models.
    Called on application startup.
    """
    Base.metadata.create_all(bind=engine)
