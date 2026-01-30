from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.api.deps import get_session
from src.db.models import Order
from src.schemas.order import OrderVerifyRequest

class OrderService:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def create_order(self, request: OrderVerifyRequest):
        # Convert Pydantic items to dicts
        items_data = [item.model_dump(mode='json') for item in request.items]
        
        new_order = Order(
            restaurant_id=request.restaurant_id,
            date=date.today(),
            status="VERIFIED",
            items=items_data
        )
        self.session.add(new_order)
        await self.session.commit()
        await self.session.refresh(new_order)
        return new_order
