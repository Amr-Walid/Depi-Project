"""
Alerts router — CRUD operations for user price alerts.
All endpoints require JWT authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.alert import Alert
from app.services.auth_service import get_current_user
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


# ──────────────────────────────────────────────
# GET /api/v1/alerts
# ──────────────────────────────────────────────
@router.get("", response_model=List[AlertResponse])
def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all price alerts for the current user."""
    return db.query(Alert).filter(Alert.user_id == current_user.id).all()


# ──────────────────────────────────────────────
# POST /api/v1/alerts
# ──────────────────────────────────────────────
@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    request: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new price alert.
    
    - `condition`: must be 'above' or 'below'
    - `threshold`: the price level to trigger the alert
    """
    alert = Alert(
        user_id=current_user.id,
        symbol=request.symbol.upper(),
        condition=request.condition,
        threshold=request.threshold,
        is_active=True,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


# ──────────────────────────────────────────────
# PUT /api/v1/alerts/{id}
# ──────────────────────────────────────────────
@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    request: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing price alert.
    
    Only fields provided in the request body will be updated.
    """
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    # Update only provided fields
    if request.symbol is not None:
        alert.symbol = request.symbol.upper()
    if request.condition is not None:
        alert.condition = request.condition
    if request.threshold is not None:
        alert.threshold = request.threshold
    if request.is_active is not None:
        alert.is_active = request.is_active

    db.commit()
    db.refresh(alert)
    return alert


# ──────────────────────────────────────────────
# DELETE /api/v1/alerts/{id}
# ──────────────────────────────────────────────
@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a price alert."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    db.delete(alert)
    db.commit()
