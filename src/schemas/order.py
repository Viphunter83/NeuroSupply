
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from src.db.models import OrderStatus

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    product_name_vn: Optional[str] = None
    image_url: Optional[str] = None
    unit: str
    quantity: float
    predicted_usage: float
    stock: float

class OrderResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    created_at: datetime
    status: OrderStatus
    items: List[OrderItem]

    class Config:
        from_attributes = True

class OrderConfirmRequest(BaseModel):
    pass

class OrderUpdate(BaseModel):
    items: List[OrderItem]
