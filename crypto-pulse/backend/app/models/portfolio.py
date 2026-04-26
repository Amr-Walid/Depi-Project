"""
SQLAlchemy ORM model for the 'portfolios' table.
Matches Karim's schema.sql definition.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    quantity = Column(Numeric(18, 8), nullable=False)
    avg_buy_price = Column(Numeric(18, 8), nullable=False)

    # Relationship
    user = relationship("User", back_populates="portfolios")
