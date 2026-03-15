import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iiko_id: Mapped[str] = mapped_column(String, index=True, nullable=False) # "Код" can be string or uuid, keeping string for safety map to Excel
    name_ru: Mapped[str] = mapped_column(String, nullable=False)
    name_vn: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    package_size: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True) # e.g. 0.4 (kg) or 24 (pcs)
    package_unit: Mapped[Optional[str]] = mapped_column(String, nullable=True) # e.g. "kg", "box"
    shelf_life_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self):
        return f"<Product {self.name_ru}>"

class TechCard(Base):
    __tablename__ = "tech_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iiko_dish_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    gross_amount: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)

    product: Mapped["Product"] = relationship("Product")

class EmpiricalRecipe(Base):
    __tablename__ = "empirical_recipes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("restaurants.id"), nullable=True) # Optional for global fallback
    dish_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    dish_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    ingredient_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id"), nullable=True)
    yield_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class StockBalance(Base):
    __tablename__ = "stock_balances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Fixing type error in thought process: TDD said Timestamp, I put UUID here by mistake.
    # Let me correct this in the next tool call properly or just fix it now. 
    # Wait, I can't edit in thought. I will correct it in the file content below.

