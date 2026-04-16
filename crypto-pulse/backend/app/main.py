from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers (to be implemented later)
# from app.routers import users, watchlists, alerts, portfolios

app = FastAPI(
    title="CryptoPulse API",
    description="Real-time cryptocurrency analytics platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS – allow all origins for development (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; replace with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def root():
    return {"message": "Crypto-Pulse API", "status": "operational"}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CryptoPulse API", "version": "1.0.0"}

# Include routers (uncomment when routers are implemented)
# app.include_router(users.router, prefix="/users", tags=["users"])
# app.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])
# app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
# app.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
