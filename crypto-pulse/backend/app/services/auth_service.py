"""
Authentication service — handles password hashing, JWT creation/validation,
and user authentication logic.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.database import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken

# ──────────────────────────────────────────────
# Password Hashing (bcrypt)
# ──────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ──────────────────────────────────────────────
# OAuth2 scheme — extracts Bearer token from header
# ──────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ──────────────────────────────────────────────
# Password utilities
# ──────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt. Truncates to 72 bytes (bcrypt limit)."""
    return pwd_context.hash(password[:72])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password[:72], hashed_password)


# ──────────────────────────────────────────────
# JWT Token creation
# ──────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload to encode (must include 'sub' for user identification)
        expires_delta: Custom expiration time (defaults to ACCESS_TOKEN_EXPIRE_MINUTES)
    
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int, db: Session) -> str:
    """
    Create a refresh token, store it in the database, and return the JWT string.
    
    Args:
        user_id: The ID of the user to create a token for
        db: SQLAlchemy session
    
    Returns:
        Encoded JWT refresh token string
    """
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_data = {
        "sub": str(user_id),
        "exp": expires_at,
        "type": "refresh",
        "jti": str(uuid.uuid4()),  # Unique token ID for revocation
    }
    token_str = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    # Store in database for revocation support
    db_token = RefreshToken(
        user_id=user_id,
        token=token_str,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(db_token)
    db.commit()

    return token_str


# ──────────────────────────────────────────────
# JWT Token decoding
# ──────────────────────────────────────────────
def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT string to decode
    
    Returns:
        Decoded payload dictionary
    
    Raises:
        HTTPException 401 if token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ──────────────────────────────────────────────
# FastAPI Dependencies
# ──────────────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the current user
    from the Authorization header.
    
    Usage:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            ...
    """
    payload = decode_token(token)

    # Ensure it's an access token, not a refresh token
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# ──────────────────────────────────────────────
# Authentication helpers
# ──────────────────────────────────────────────
def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    """
    Verify user credentials.
    
    Args:
        email: User's email address
        password: Plain-text password to verify
        db: SQLAlchemy session
    
    Returns:
        User object if credentials are valid, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
