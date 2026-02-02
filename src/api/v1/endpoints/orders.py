from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps import get_session, get_current_user
from src.services.order_service import OrderService
from src.schemas.order import OrderResponse
from src.db.models.user import User

router = APIRouter()

@router.get("/latest", response_model=OrderResponse)
async def get_latest_order(
    restaurant_id: UUID = Query(None), # Optional, if provided, strict check? Or override?
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Get latest draft order.
    If 'restaurant_id' is NOT provided, use current_user.linked_restaurant.
    """
    target_rest_id = restaurant_id or current_user.linked_restaurant_id
    
    if not target_rest_id:
        raise HTTPException(status_code=400, detail="No restaurant linked to user")

    service = OrderService(db)
    # 1. Try to find existing DRAFT
    order = await service.get_latest_draft_order(target_rest_id)
    if order:
        return order

    # 2. If no draft, check if we can generate one from Sales Plan
    from datetime import date
    from sqlalchemy import select
    from src.db.models import SalesPlan
    
    # Check for today's plan
    today = date.today()
    stmt = select(SalesPlan).where(
        SalesPlan.restaurant_id == target_rest_id,
        SalesPlan.date == today
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    
    if plan and plan.amount_rub > 0:
        # Generate new order
        new_order = await service.generate_draft_order(target_rest_id, float(plan.amount_rub))
        return new_order

    # 3. If no plan, we can't generate.
    raise HTTPException(status_code=404, detail="No draft order found and no Sales Plan for today to generate one.")

@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: UUID, 
    db: AsyncSession = Depends(get_session)
):
    service = OrderService(db)
    return await service.confirm_order(order_id)

from src.schemas.order import OrderUpdate

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    update_data: OrderUpdate,
    db: AsyncSession = Depends(get_session)
):
    service = OrderService(db)
    items_dicts = [item.model_dump() for item in update_data.items]
    return await service.update_order_items(order_id, items_dicts)

@router.get("/{order_id}/export/excel")
async def export_order_excel(
    order_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    service = OrderService(db)
    file_stream = await service.export_order_to_excel(order_id)
    
    filename = f"Order_{str(order_id)[:8]}.xlsx"
    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
