from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

from src.api.deps import get_session
from src.schemas.order import OrderDraftResponse, OrderItemDraft
from src.db.models import Product

class CalculationService:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def calculate_draft(self, restaurant_id: UUID) -> OrderDraftResponse:
        # Fetch all products (limit for now)
        stmt = select(Product).limit(50)
        result = await self.session.execute(stmt)
        products = result.scalars().all()
        
        items = []
        for p in products:
            items.append(OrderItemDraft(
                product_id=p.id,
                product_name_ru=p.name_ru,
                product_name_vn=p.name_vn if p.name_vn else "",
                unit=p.unit,
                amount_needed=10.0, # Dummy logic
                current_stock=5.0,  # Dummy logic
                forecast_sales=15.0 # Dummy logic
            ))
            
        return OrderDraftResponse(
            date=date.today(),
            restaurant_id=restaurant_id,
            items=items
        )
