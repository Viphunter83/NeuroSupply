
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import date, datetime, timedelta
import logging
import uuid

from src.api.deps import get_session, get_current_user
from src.db.models import User, SalesPlan, Restaurant
from src.services.calculation.engine_v2 import CalculationEngineV2
from src.services.iiko.client import IikoClient

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/forecast-vs-fact")
async def get_forecast_vs_fact(
    restaurant_id: uuid.UUID = Query(None),
    date_from: date = Query(None),
    date_to: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Returns daily comparison of Sales Plan vs Actual Sales (Fact).
    Fact is mocked or fetched from iiko (future).
    """
    target_rest_id = restaurant_id or current_user.linked_restaurant_id
    if not target_rest_id:
        raise HTTPException(status_code=400, detail="No restaurant linked")

    # Defaults: current month
    if not date_from:
        today = date.today()
        date_from = date(today.year, today.month, 1)
    if not date_to:
        import calendar
        last_day = calendar.monthrange(date_from.year, date_from.month)[1]
        date_to = date(date_from.year, date_from.month, last_day)

    # 1. Fetch Plans
    stmt = select(SalesPlan).where(
        SalesPlan.restaurant_id == target_rest_id,
        SalesPlan.date >= date_from,
        SalesPlan.date <= date_to
    ).order_by(SalesPlan.date)
    
    result = await db.execute(stmt)
    plans = result.scalars().all()
    
    # 2. Fetch Fact (Mock for now, or use IikoClient)
    # Ideally: IikoClient().get_sales_olap(...)
    # For MVP Integration Task: Return 0 or Mock
    
    data = []
    
    # Find restaurant settings/iiko_id for connection
    r_res = await db.execute(select(Restaurant).where(Restaurant.id == target_rest_id))
    restaurant = r_res.scalar_one_or_none()
    
    if not restaurant:
         raise HTTPException(status_code=404, detail="Restaurant not found")

    # MOCK FACT DATA GENERATION (To show something on graph)
    # TODO: Connect to real Iiko OLAP
    import random
    
    plan_map = {p.date: float(p.amount_rub) for p in plans}
    
    # Iterate through range
    delta = date_to - date_from
    for i in range(delta.days + 1):
        d = date_from + timedelta(days=i)
        
        plan_val = plan_map.get(d, 0.0)
        
        # Mock Fact: Random fluctuation around plan if past/today, else 0
        fact_val = 0.0
        if d <= date.today():
             # +/- 20%
             if plan_val > 0:
                fact_val = plan_val * random.uniform(0.8, 1.2)
        
        data.append({
            "date": d.strftime("%Y-%m-%d"),
            "plan": plan_val,
            "fact": fact_val
        })
        
    return {"data": data}

@router.get("/prep-plan")
async def get_prep_plan(
    restaurant_id: uuid.UUID = Query(None),
    plan_amount: float = Query(None), # Optional override
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Returns the detailed preparation plan (Calculation results).
    Doesn't create an order, just calculates.
    """
    target_rest_id = restaurant_id or current_user.linked_restaurant_id
    if not target_rest_id:
        raise HTTPException(status_code=400, detail="No restaurant linked")

    engine = CalculationEngineV2(db)
    
    try:
        # If plan_amount not provided, get today's plan
        if plan_amount is None:
            stmt = select(SalesPlan).where(
                SalesPlan.restaurant_id == target_rest_id,
                SalesPlan.date == date.today()
            )
            res = await db.execute(stmt)
            sp = res.scalar_one_or_none()
            if sp:
                plan_amount = float(sp.amount_rub)
            else:
                plan_amount = 0.0
        
        results = await engine.calculate_needs(target_rest_id, plan_amount)
        return {"items": results, "plan_source": plan_amount}
        
    except Exception as e:
        logger.error(f"Error calculating prep plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
