"""
Portfolios router — CRUD operations for user investment portfolios.
All endpoints require JWT authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services.auth_service import get_current_user
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate, PortfolioResponse

router = APIRouter(prefix="/api/v1/portfolios", tags=["Portfolios"])


# ──────────────────────────────────────────────
# GET /api/v1/portfolios
# ──────────────────────────────────────────────
@router.get("", response_model=List[PortfolioResponse])
def list_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all positions in the current user's portfolio."""
    return db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()


# ──────────────────────────────────────────────
# POST /api/v1/portfolios
# ──────────────────────────────────────────────
@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def add_position(
    request: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a new position to the user's portfolio.
    
    - `symbol`: Trading pair (e.g., 'BTCUSDT')
    - `quantity`: Amount of the coin held
    - `avg_buy_price`: Average purchase price
    """
    position = Portfolio(
        user_id=current_user.id,
        symbol=request.symbol.upper(),
        quantity=request.quantity,
        avg_buy_price=request.avg_buy_price,
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


# ──────────────────────────────────────────────
# PUT /api/v1/portfolios/{id}
# ──────────────────────────────────────────────
@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_position(
    portfolio_id: int,
    request: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing portfolio position.
    
    Only fields provided in the request body will be updated.
    """
    position = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id,
    ).first()

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio position not found"
        )

    if request.quantity is not None:
        position.quantity = request.quantity
    if request.avg_buy_price is not None:
        position.avg_buy_price = request.avg_buy_price

    db.commit()
    db.refresh(position)
    return position


# ──────────────────────────────────────────────
# DELETE /api/v1/portfolios/{id}
# ──────────────────────────────────────────────
@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a position from the user's portfolio."""
    position = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id,
    ).first()

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio position not found"
        )

    db.delete(position)
    db.commit()
