import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_session, require_role
from src.db.models.user import User, UserRole
from src.db.models.order import Order, OrderStatus
from src.db.models.product import Product
from src.db.models.analytics import Anomalies

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def list_anomalies(
    restaurant_id: uuid.UUID = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List all anomalies for the restaurant.
    """
    require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)
    
    target_rest_id = restaurant_id or current_user.linked_restaurant_id
    if not target_rest_id:
        raise HTTPException(status_code=400, detail="No restaurant linked")
        
    stmt = (
        select(
            Anomalies.id,
            Anomalies.order_id,
            Anomalies.product_id,
            Anomalies.auto_qty,
            Anomalies.manual_qty,
            Anomalies.reason,
            Anomalies.created_at,
            Product.name_ru,
            Product.name_vn,
            Product.unit,
            Order.status.label("order_status")
        )
        .join(Order, Anomalies.order_id == Order.id)
        .join(Product, Anomalies.product_id == Product.id)
        .where(Order.restaurant_id == target_rest_id)
        .order_by(Anomalies.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        {
            "id": str(r.id),
            "order_id": str(r.order_id),
            "product_id": str(r.product_id),
            "product_name": r.name_ru,
            "product_name_vn": r.name_vn or "",
            "unit": r.unit,
            "auto_qty": float(r.auto_qty),
            "manual_qty": float(r.manual_qty),
            "diff": float(r.manual_qty - r.auto_qty),
            "reason": r.reason or "",
            "created_at": r.created_at.isoformat(),
            "order_status": r.order_status
        }
        for r in rows
    ]

@router.post("/{anomaly_id}/approve")
async def approve_anomaly(
    anomaly_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Approve an anomaly (effectively approves the linked order).
    """
    require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)
    
    stmt = select(Anomalies).where(Anomalies.id == anomaly_id)
    res = await db.execute(stmt)
    anomaly = res.scalar_one_or_none()
    
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
        
    order_stmt = select(Order).where(Order.id == anomaly.order_id)
    order_res = await db.execute(order_stmt)
    order = order_res.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Linked order not found")
        
    if order.status == OrderStatus.VERIFIED_BY_COOK:
        order.status = OrderStatus.APPROVED_BY_MANAGER
        await db.commit()
        return {"status": "success", "new_order_status": order.status}
    
    return {"status": "no_change", "order_status": order.status}
