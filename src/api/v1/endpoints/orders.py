"""
Order API Endpoints — all require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_session, require_role
from src.db.models.user import User, UserRole
from src.db.models.order import Order, OrderStatus
from src.schemas.order import OrderResponse, OrderUpdate
from src.services.order_service import OrderService

router = APIRouter()


@router.get("/")
async def list_orders(
    restaurant_id: UUID = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List orders (Manager or Admin). Filters by restaurant_id if provided."""
    require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)
    
    target_rest_id = restaurant_id or current_user.linked_restaurant_id
    
    stmt = select(Order)
    if target_rest_id:
        stmt = stmt.where(Order.restaurant_id == target_rest_id)
        
    stmt = stmt.order_by(Order.created_at.desc())
    res = await db.execute(stmt)
    orders = res.scalars().all()
    
    # We need to include restaurant info and items count
    from src.db.models.restaurant import Restaurant
    result = []
    for o in orders:
        rest_stmt = select(Restaurant).where(Restaurant.id == o.restaurant_id)
        rest = (await db.execute(rest_stmt)).scalar_one_or_none()
        result.append({
            "id": str(o.id),
            "restaurant_name": rest.name if rest else "Unknown",
            "status": o.status.value,
            "items_count": len(o.items) if o.items else 0,
            "created_at": o.created_at.isoformat(),
            "items": o.items # Full items for details view if needed
        })
    return result


@router.get("/latest", response_model=OrderResponse)
async def get_latest_order(
    restaurant_id: UUID = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get latest draft order.
    If 'restaurant_id' is NOT provided, use current_user.linked_restaurant.
    """
    target_rest_id = restaurant_id or current_user.linked_restaurant_id

    if not target_rest_id:
        raise HTTPException(status_code=400, detail="No restaurant linked to user")

    service = OrderService(db)

    # 1. Try to find existing ACTIVE (DRAFT or VERIFIED)
    order = await service.get_active_order(target_rest_id)
    if order:
        return order

    # 2. If no draft, check if we can generate one from Sales Plan
    from datetime import date

    from src.db.models import SalesPlan

    today = date.today()
    stmt = select(SalesPlan).where(
        SalesPlan.restaurant_id == target_rest_id,
        SalesPlan.date == today,
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()

    if plan and plan.amount_rub > 0:
        new_order = await service.generate_draft_order(
            target_rest_id, float(plan.amount_rub)
        )
        return new_order

    raise HTTPException(
        status_code=404,
        detail="No draft order found and no Sales Plan for today to generate one.",
    )


@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Confirm an order (Cook or Admin only)."""
    require_role(current_user, UserRole.COOK, UserRole.ADMIN)
    service = OrderService(db)
    return await service.confirm_order(order_id)


@router.post("/{order_id}/approve", response_model=OrderResponse)
async def approve_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Approve an order (Manager or Admin only)."""
    require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)
    service = OrderService(db)
    return await service.approve_order(order_id)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    update_data: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Update order items (Cook or Admin only)."""
    require_role(current_user, UserRole.COOK, UserRole.ADMIN)
    service = OrderService(db)
    items_dicts = [item.model_dump() for item in update_data.items]
    return await service.update_order_items(order_id, items_dicts)


@router.get("/{order_id}/export/excel")
async def export_order_excel(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Export order to Excel (Manager or Admin only)."""
    require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)
    service = OrderService(db)
    file_stream = await service.export_order_to_excel(order_id)

    filename = f"Order_{str(order_id)[:8]}.xlsx"
    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
