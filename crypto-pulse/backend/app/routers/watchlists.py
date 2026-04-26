"""
Watchlists router — CRUD operations for user watchlists.
All endpoints require JWT authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.auth_service import get_current_user
from app.schemas.watchlist import WatchlistCreate, WatchlistResponse

router = APIRouter(prefix="/api/v1/watchlists", tags=["Watchlists"])


# ──────────────────────────────────────────────
# GET /api/v1/watchlists
# ──────────────────────────────────────────────
@router.get("", response_model=List[WatchlistResponse])
def list_watchlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all coins in the current user's watchlist."""
    return db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()


# ──────────────────────────────────────────────
# POST /api/v1/watchlists
# ──────────────────────────────────────────────
@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    request: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a coin to the current user's watchlist.
    
    Returns 400 if the coin is already in the watchlist.
    """
    # Check for duplicates
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == request.symbol.upper(),
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{request.symbol.upper()}' is already in your watchlist"
        )

    watchlist_item = Watchlist(
        user_id=current_user.id,
        symbol=request.symbol.upper(),
    )
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    return watchlist_item


# ──────────────────────────────────────────────
# DELETE /api/v1/watchlists/{id}
# ──────────────────────────────────────────────
@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a coin from the current user's watchlist."""
    item = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id,
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found"
        )

    db.delete(item)
    db.commit()
