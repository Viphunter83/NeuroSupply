from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps import get_session
from src.services.order_service import OrderService
from src.schemas.order import OrderResponse

router = APIRouter()

@router.get("/latest", response_model=OrderResponse)
async def get_latest_order(
    restaurant_id: UUID, 
    db: AsyncSession = Depends(get_session)
):
    service = OrderService(db)
    order = await service.get_latest_draft_order(restaurant_id)
    if not order:
        raise HTTPException(status_code=404, detail="No draft order found")
    return order

@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: UUID, 
    db: AsyncSession = Depends(get_session)
):
    service = OrderService(db)
    return await service.confirm_order(order_id)
