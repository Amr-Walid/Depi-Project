"""
Pydantic schemas for watchlist endpoints.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WatchlistCreate(BaseModel):
    """Request body to add a coin to watchlist."""
    symbol: str

    model_config = {
        "json_schema_extra": {
            "examples": [{"symbol": "BTCUSDT"}]
        }
    }


class WatchlistResponse(BaseModel):
    """Watchlist item returned by API."""
    id: int
    user_id: int
    symbol: str
    added_at: datetime

    model_config = {"from_attributes": True}
