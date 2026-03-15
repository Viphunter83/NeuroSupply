from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class RestaurantSettings(BaseModel):
    safety_stock_ratio: float = Field(default=1.1, description="Коэффициент страхового запаса (например, 1.1 для +10%)")
    days_in_transit: int = Field(default=0, description="Количество дней в пути для заказов")
    iiko_terminal_group_id: Optional[UUID] = None

class RestaurantBase(BaseModel):
    name: str
    iiko_id: UUID

class RestaurantResponse(RestaurantBase):
    id: UUID
    settings: RestaurantSettings

    class Config:
        from_attributes = True

class RestaurantSettingsUpdate(BaseModel):
    settings: RestaurantSettings
