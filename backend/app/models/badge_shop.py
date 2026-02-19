"""
Badge Shop: models for listing badges for sale and tracking purchases.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class BadgeShopItem(Base):
    __tablename__ = "badge_shop_items"

    id = Column(Integer, primary_key=True, index=True)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    price_type = Column(String(20), nullable=False)   # gold | mana | thankyou
    price_amount = Column(Integer, nullable=False, default=10)
    stock = Column(Integer, nullable=True)             # NULL = unlimited
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    badge = relationship("Badge")
    purchases = relationship("BadgeShopPurchase", back_populates="shop_item")


class BadgeShopPurchase(Base):
    __tablename__ = "badge_shop_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shop_item_id = Column(Integer, ForeignKey("badge_shop_items.id"), nullable=False)
    price_type = Column(String(20), nullable=False)
    price_amount = Column(Integer, nullable=False)
    purchased_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    shop_item = relationship("BadgeShopItem", back_populates="purchases")
