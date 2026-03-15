import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Numeric, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class ProductMix(Base):
    """
    Validation / Forecasting stats: how many items of a specific dish 
    are sold per 1000 RUB of revenue.
    """
    __tablename__ = "product_mix"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    
    # We link to a "Dish" (which might be just a name/code in this MVP or a full Product)
    # Ideally should be a separate Dishes entity vs Ingredients (Products), 
    # but for simplicity we might reuse Product or just store iiko_dish_id/name.
    # Let's assume we map 'Dish' to 'Product' if it's a sellable item, 
    # OR strictly use iiko_dish_id if we don't store Dishes in our DB yet.
    # Given the prompt says "Entry: 50 pcs Soup Pho", let's store it as:
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=True) # If mapped
    iiko_dish_id: Mapped[str] = mapped_column(String, nullable=True) # If unmapped
    
    probability: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False) # Qty per 1000 RUB

class SalesFact(Base):
    """
    Daily sales data per dish from iiko.
    """
    __tablename__ = "sales_facts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    iiko_dish_id: Mapped[str] = mapped_column(String, nullable=False)
    dish_name: Mapped[str] = mapped_column(String, nullable=False)
    
    date: Mapped[date] = mapped_column(DateTime, nullable=False) # Store date part
    quantity: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    revenue_rub: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

class Anomalies(Base):
    """
    Tracking manual deviations from the calculated order.
    """
    __tablename__ = "anomalies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    
    auto_qty: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    manual_qty: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(datetime.UTC))
