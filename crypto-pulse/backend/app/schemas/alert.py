"""
Pydantic schemas for alert endpoints.
"""
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class AlertCreate(BaseModel):
    """Request body to create a price alert."""
    symbol: str
    condition: str      # 'above' or 'below'
    threshold: float

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v):
        if v not in ("above", "below"):
            raise ValueError("condition must be 'above' or 'below'")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "condition": "above",
                    "threshold": 70000.0
                }
            ]
        }
    }


class AlertUpdate(BaseModel):
    """Request body to update an existing alert."""
    symbol: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    is_active: Optional[bool] = None

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v):
        if v is not None and v not in ("above", "below"):
            raise ValueError("condition must be 'above' or 'below'")
        return v


class AlertResponse(BaseModel):
    """Alert item returned by API."""
    id: int
    user_id: int
    symbol: str
    condition: str
    threshold: float
    is_active: bool

    model_config = {"from_attributes": True}
