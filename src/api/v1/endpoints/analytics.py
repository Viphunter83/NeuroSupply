"""
Analytics API Endpoints.
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_session
from src.db.models import Restaurant, SalesPlan, User
from src.db.models.analytics import SalesFact
from src.services.calculation.engine_v2 import CalculationEngineV2

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/forecast-vs-fact")
async def get_forecast_vs_fact(
    restaurant_id: uuid.UUID = Query(None),
    date_from: date = Query(None),
    date_to: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Returns daily comparison of Sales Plan vs Actual Sales (Fact).
    Fact data is fetched from the SalesFact table.
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
    stmt = (
        select(SalesPlan)
        .where(
            SalesPlan.restaurant_id == target_rest_id,
            SalesPlan.date >= date_from,
            SalesPlan.date <= date_to,
        )
        .order_by(SalesPlan.date)
    )
    result = await db.execute(stmt)
    plans = result.scalars().all()

    # 2. Fetch real Fact data from SalesFact (daily aggregated revenue)
    stmt_fact = (
        select(
            func.date(SalesFact.date).label("fact_date"),
            func.sum(SalesFact.revenue_rub).label("total_revenue"),
        )
        .where(
            SalesFact.restaurant_id == target_rest_id,
            func.date(SalesFact.date) >= date_from,
            func.date(SalesFact.date) <= date_to,
        )
        .group_by(func.date(SalesFact.date))
    )
    result_fact = await db.execute(stmt_fact)
    fact_rows = result_fact.all()
    fact_map = {row.fact_date: float(row.total_revenue) for row in fact_rows}

    # 3. Build response
    plan_map = {p.date: float(p.amount_rub) for p in plans}
    data = []

    delta = date_to - date_from
    for i in range(delta.days + 1):
        d = date_from + timedelta(days=i)
        plan_val = plan_map.get(d, 0.0)
        fact_val = fact_map.get(d, 0.0)

        data.append(
            {
                "date": d.strftime("%Y-%m-%d"),
                "plan": plan_val,
                "fact": fact_val,
            }
        )

    return {"data": data}


@router.get("/prep-plan")
async def get_prep_plan(
    restaurant_id: uuid.UUID = Query(None),
    plan_amount: float = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
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
        if plan_amount is None:
            stmt = select(SalesPlan).where(
                SalesPlan.restaurant_id == target_rest_id,
                SalesPlan.date == date.today(),
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
