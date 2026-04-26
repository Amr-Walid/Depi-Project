"""
CryptoPulse API — Main Application Entry Point

Real-time cryptocurrency analytics platform.
Provides authentication, coin data, watchlists, alerts, and portfolio management.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers import auth, coins, watchlists, alerts, portfolios

# ──────────────────────────────────────────────
# Application Setup
# ──────────────────────────────────────────────
app = FastAPI(
    title="CryptoPulse API",
    description=(
        "Real-time cryptocurrency analytics platform powered by Azure, Kafka, and Spark.\n\n"
        "## Features\n"
        "- 🔐 JWT Authentication (signup, login, token refresh)\n"
        "- 📊 Coin data & market overview\n"
        "- ⭐ Watchlists management\n"
        "- 🔔 Price alerts\n"
        "- 💼 Portfolio tracking\n\n"
        "## Authentication\n"
        "1. Register via `POST /api/v1/auth/signup`\n"
        "2. Login via `POST /api/v1/auth/login`\n"
        "3. Use the returned `access_token` as a Bearer token in the Authorization header"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ──────────────────────────────────────────────
# CORS Middleware — allow all origins for development
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; replace with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Startup Event — create database tables
# ──────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    """Create all database tables on application startup."""
    create_tables()


# ──────────────────────────────────────────────
# Root & Health Check
# ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Root endpoint — confirms the API is operational."""
    return {"message": "Crypto-Pulse API", "status": "operational"}


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "ok", "service": "CryptoPulse API", "version": "1.0.0"}


# ──────────────────────────────────────────────
# Register Routers
# ──────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(coins.router)
app.include_router(watchlists.router)
app.include_router(alerts.router)
app.include_router(portfolios.router)
