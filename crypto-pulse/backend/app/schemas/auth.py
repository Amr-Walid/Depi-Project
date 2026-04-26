"""
Pydantic schemas for authentication endpoints.
Defines request/response models for signup, login, and token operations.
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ──────────────────────────────────────────────
# Request Schemas
# ──────────────────────────────────────────────
class SignupRequest(BaseModel):
    """Request body for user registration."""
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "securepassword123"
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """Request body for user login."""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


# ──────────────────────────────────────────────
# Response Schemas
# ──────────────────────────────────────────────
class TokenResponse(BaseModel):
    """Response containing JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user information returned by API."""
    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
