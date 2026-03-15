from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
import uuid
from datetime import date

from src.api import deps
from src.db.models import SalesPlan as SalesPlanModel
from src.db.models.user import UserRole
from src.schemas.sales_plan import SalesPlan, SalesPlanCreate, SalesPlanBulkCreate

router = APIRouter()

@router.get("/", response_model=List[SalesPlan])
async def get_sales_plans(
    restaurant_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(deps.get_session),
    current_user = Depends(deps.get_current_user),
):
    """
    Get sales plans for a restaurant in a date range.
    """
    # Authorization: User must be linked to this restaurant OR be an admin
    if current_user.role != UserRole.ADMIN and current_user.linked_restaurant_id != restaurant_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    stmt = select(SalesPlanModel).where(
        SalesPlanModel.restaurant_id == restaurant_id,
        SalesPlanModel.date >= start_date,
        SalesPlanModel.date <= end_date
    ).order_by(SalesPlanModel.date)
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/bulk", response_model=List[SalesPlan])
async def create_sales_plans_bulk(
    data: SalesPlanBulkCreate,
    db: AsyncSession = Depends(deps.get_session),
    current_user = Depends(deps.get_current_user),
):
    """
    Create or update sales plans in bulk.
    """
    # Manager or Admin role required
    deps.require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)

    results = []
    for plan_in in data.plans:
        # Check if exists
        stmt = select(SalesPlanModel).where(
            SalesPlanModel.restaurant_id == plan_in.restaurant_id,
            SalesPlanModel.date == plan_in.date
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        
        if existing:
            existing.amount_rub = plan_in.amount_rub
            db.add(existing)
            results.append(existing)
        else:
            new_plan = SalesPlanModel(
                restaurant_id=plan_in.restaurant_id,
                date=plan_in.date,
                amount_rub=plan_in.amount_rub
            )
            db.add(new_plan)
            results.append(new_plan)

    await db.commit()
    for r in results:
        await db.refresh(r)
    return results

@router.delete("/{plan_id}")
async def delete_sales_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_session),
    current_user = Depends(deps.get_current_user),
):
    """
    Delete a single sales plan.
    """
    deps.require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)
    
    stmt = delete(SalesPlanModel).where(SalesPlanModel.id == plan_id)
    await db.execute(stmt)
    await db.commit()
    return {"status": "success"}
