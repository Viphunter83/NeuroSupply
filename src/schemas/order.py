from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import date

class OrderItemDraft(BaseModel):
    product_id: UUID
    product_name_ru: str
    product_name_vn: Optional[str]
    unit: str
    amount_needed: float
    current_stock: float
    forecast_sales: float

class OrderDraftResponse(BaseModel):
    date: date
    restaurant_id: UUID
    items: List[OrderItemDraft]

class OrderVerifyItem(BaseModel):
    product_id: UUID
    amount: float

class OrderVerifyRequest(BaseModel):
    restaurant_id: UUID
    items: List[OrderVerifyItem]
