from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
import uuid

class SalesPlanBase(BaseModel):
    restaurant_id: uuid.UUID
    date: date
    amount_rub: float

class SalesPlanCreate(SalesPlanBase):
    pass

class SalesPlanUpdate(BaseModel):
    amount_rub: float

class SalesPlan(SalesPlanBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SalesPlanBulkCreate(BaseModel):
    plans: List[SalesPlanCreate]
