
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
from typing import List

from src.db.session import get_db
from src.db.models import Order, OrderStatus
from src.schemas.order import OrderResponse, OrderConfirmRequest

router = APIRouter()

from src.services.order_service import OrderService

@router.get("/latest", response_model=OrderResponse)
async def get_latest_order(restaurant_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get the latest draft order for a restaurant.
    """
    service = OrderService(db)
    order = await service.get_latest_draft_order(restaurant_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="No draft orders found")
    
    return order

@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(order_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Confirm an order (change status to VERIFIED_BY_COOK).
    """
    service = OrderService(db)
    return await service.confirm_order(order_id)
