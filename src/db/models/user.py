import enum
from typing import Optional
from sqlalchemy import BigInteger, ForeignKey, Enum, String
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

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True)
    supabase_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), unique=True, nullable=True)
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.COOK)
    linked_restaurant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=True)

    restaurant = relationship("Restaurant")
