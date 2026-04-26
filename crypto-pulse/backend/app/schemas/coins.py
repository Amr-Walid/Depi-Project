"""
Pydantic schemas for coin data endpoints.
Defines response models for coin listings, summaries, prices, and market overview.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CoinInfo(BaseModel):
    """Basic information about a supported cryptocurrency."""
    symbol: str
    name: str
    is_active: bool = True


class CoinSummary(BaseModel):
    """Daily summary for a single coin (matches Gold Layer coin_daily_summary)."""
    symbol: str
    trading_date: str
    day_open: float
    day_close: float
    day_high: float
    day_low: float
    total_volume: float
    avg_price: float
    price_change_pct: float
    tick_count: int


class CoinPrice(BaseModel):
    """A single price data point."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class CoinPriceHistory(BaseModel):
    """Historical price data for a coin."""
    symbol: str
    days: int
    prices: List[CoinPrice]


class MarketOverview(BaseModel):
    """Market-wide overview statistics."""
    total_market_cap: float
    total_volume_24h: float
    btc_dominance: float
    active_coins: int
    top_gainers: List[dict]
    top_losers: List[dict]
    last_updated: str
