import enum
from typing import Optional
from sqlalchemy import BigInteger, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class UserRole(str, enum.Enum):
    COOK = "cook"
    MANAGER = "manager"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.COOK)
    linked_restaurant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("restaurants.id"), nullable=True)

    restaurant = relationship("Restaurant")
