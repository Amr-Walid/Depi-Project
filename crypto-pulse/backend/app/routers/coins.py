"""
Coins router — provides cryptocurrency data endpoints.
All endpoints require JWT authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List

from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.data_service import (
    get_supported_coins,
    get_coin_summary,
    get_coin_prices,
    get_market_overview,
)
from app.schemas.coins import CoinInfo, CoinSummary, CoinPriceHistory, MarketOverview

router = APIRouter(prefix="/api/v1", tags=["Coins & Market Data"])


# ──────────────────────────────────────────────
# GET /api/v1/coins
# ──────────────────────────────────────────────
@router.get("/coins", response_model=List[CoinInfo])
def list_coins(current_user: User = Depends(get_current_user)):
    """
    Get a list of all supported cryptocurrency coins.
    
    Returns the symbol, name, and active status for each coin
    tracked by CryptoPulse.
    """
    return get_supported_coins()


# ──────────────────────────────────────────────
# GET /api/v1/coins/{symbol}/summary
# ──────────────────────────────────────────────
@router.get("/coins/{symbol}/summary", response_model=CoinSummary)
def coin_summary(symbol: str, current_user: User = Depends(get_current_user)):
    """
    Get the daily trading summary for a specific coin.
    
    Includes: open, close, high, low prices, total volume,
    average price, price change percentage, and tick count.
    
    When Gold Layer is ready, this pulls from the `coin_daily_summary` dbt model.
    """
    summary = get_coin_summary(symbol)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin '{symbol.upper()}' not found. Use GET /api/v1/coins to see supported coins."
        )
    return summary


# ──────────────────────────────────────────────
# GET /api/v1/coins/{symbol}/prices
# ──────────────────────────────────────────────
@router.get("/coins/{symbol}/prices", response_model=CoinPriceHistory)
def coin_prices(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days of history"),
    current_user: User = Depends(get_current_user),
):
    """
    Get historical OHLCV price data for a specific coin.
    
    - `days`: Number of days of history (1–365, default: 30)
    
    When Gold Layer is ready, this pulls from ADLS Gen2 via the Gold tables.
    """
    prices = get_coin_prices(symbol, days)
    if not prices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin '{symbol.upper()}' not found. Use GET /api/v1/coins to see supported coins."
        )
    return prices


# ──────────────────────────────────────────────
# GET /api/v1/market/overview
# ──────────────────────────────────────────────
@router.get("/market/overview", response_model=MarketOverview)
def market_overview(current_user: User = Depends(get_current_user)):
    """
    Get a market-wide overview with aggregate statistics.
    
    Includes: total market cap, 24h volume, BTC dominance,
    top 5 gainers, and top 5 losers.
    """
    return get_market_overview()
