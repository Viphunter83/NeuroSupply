import uuid
from typing import Optional, Any
from sqlalchemy import String, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iiko_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    time_zone: Mapped[str] = mapped_column(String, nullable=False, default="Europe/Moscow")
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<Restaurant {self.name} ({self.id})>"
