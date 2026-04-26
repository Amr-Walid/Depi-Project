"""
Authentication router — handles user registration, login, token refresh, and profile.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    authenticate_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ──────────────────────────────────────────────
# POST /api/v1/auth/signup
# ──────────────────────────────────────────────
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - Validates that the email is not already taken
    - Hashes the password using bcrypt
    - Creates the user in PostgreSQL
    - Returns JWT access and refresh tokens
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        email=request.email,
        password_hash=hash_password(request.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate tokens
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(user_id=new_user.id, db=db)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ──────────────────────────────────────────────
# POST /api/v1/auth/login
# ──────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and return JWT tokens.
    
    - Verifies email exists and password matches
    - Returns JWT access and refresh tokens
    """
    user = authenticate_user(request.email, request.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(user_id=user.id, db=db)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ──────────────────────────────────────────────
# POST /api/v1/auth/refresh
# ──────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """
    Refresh an access token using a valid refresh token.
    
    - Validates the refresh token JWT
    - Checks it exists in DB and is not revoked
    - Revokes the old refresh token (rotation)
    - Returns new access and refresh tokens
    """
    # Decode the refresh token
    payload = decode_token(request.refresh_token)

    # Ensure it's a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected refresh token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check token exists in DB and is not revoked
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == request.refresh_token,
        RefreshToken.revoked == False,
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has been revoked",
        )

    # Revoke the old refresh token (token rotation for security)
    db_token.revoked = True
    db.commit()

    # Issue new tokens
    new_access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(user_id=int(user_id), db=db)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


# ──────────────────────────────────────────────
# GET /api/v1/auth/me
# ──────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the profile of the currently authenticated user.
    
    Requires a valid JWT access token in the Authorization header.
    """
    return current_user
