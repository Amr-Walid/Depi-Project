"""
Pydantic schemas for portfolio endpoints.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PortfolioCreate(BaseModel):
    """Request body to add a position to portfolio."""
    symbol: str
    quantity: float
    avg_buy_price: float

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "quantity": 0.5,
                    "avg_buy_price": 65000.0
                }
            ]
        }
    }


class PortfolioUpdate(BaseModel):
    """Request body to update a portfolio position."""
    quantity: Optional[float] = None
    avg_buy_price: Optional[float] = None


class PortfolioResponse(BaseModel):
    """Portfolio position returned by API."""
    id: int
    user_id: int
    symbol: str
    quantity: float
    avg_buy_price: float

    model_config = {"from_attributes": True}
