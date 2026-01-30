import uuid
from datetime import date, datetime
from typing import Any
from sqlalchemy import Date, ForeignKey, Numeric, DateTime, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import enum

class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    VERIFIED_BY_COOK = "verified_by_cook"
    EXPORTED_TO_PROCOB = "exported_to_procob"

class SalesPlan(Base):
    __tablename__ = "sales_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_rub: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.DRAFT)
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=[])

    restaurant = relationship("Restaurant")
