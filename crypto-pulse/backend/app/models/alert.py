"""
SQLAlchemy ORM model for the 'alerts' table.
Matches Karim's schema.sql definition.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    condition = Column(String(50), nullable=False)        # 'above' | 'below'
    threshold = Column(Numeric(18, 8), nullable=False)
    is_active = Column(Boolean, default=True, index=True)

    # Relationship
    user = relationship("User", back_populates="alerts")
