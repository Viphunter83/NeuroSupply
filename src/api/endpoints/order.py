
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
from typing import List

from src.db.session import get_db
from src.db.models import Order, OrderStatus
from src.schemas.order import OrderResponse, OrderConfirmRequest

router = APIRouter()

@router.get("/latest", response_model=OrderResponse)
async def get_latest_order(restaurant_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get the latest order for a restaurant (DRAFT preferable, else any latest).
    """
    stmt = select(Order).where(
        Order.restaurant_id == restaurant_id
    ).order_by(desc(Order.created_at)).limit(1)
    
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="No orders found")
    
    return order

@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(order_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Confirm an order (change status to VERIFIED_BY_COOK).
    """
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status != OrderStatus.DRAFT:
        # Allow re-confirming? Or error?
        # For now logic allows transitioning from Draft.
        pass
        
    order.status = OrderStatus.VERIFIED_BY_COOK
    await db.commit()
    await db.refresh(order)
    return order
