
import logging
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from src.db.models import Order, OrderStatus, Restaurant
from src.schemas.order import OrderResponse

logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_draft_order(self, restaurant_id: UUID) -> Optional[Order]:
        """
        Fetch the latest order with status DRAFT for a specific restaurant.
        """
        stmt = (
            select(Order)
            .where(
                Order.restaurant_id == restaurant_id,
                # In real app, we might also filter by status if we strictly want DRAFT
                 Order.status == OrderStatus.DRAFT
            )
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def confirm_order(self, order_id: UUID) -> Order:
        """
        Confirm an order by changing its status to VERIFIED_BY_COOK.
        """
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.DRAFT:
             # Depending on business logic, maybe allow re-confirming? 
             # For now, let's just log warning or allow it.
             logger.warning(f"Order {order_id} is already in state {order.status}")

        order.status = OrderStatus.VERIFIED_BY_COOK
        await self.db.commit()
        await self.db.refresh(order)
        
        logger.info(f"Order {order_id} confirmed (VERIFIED_BY_COOK).")
        return order
