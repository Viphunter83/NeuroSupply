import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any

from src.api.deps import get_session
from src.db.models.product import Product

router = APIRouter()

@router.get("/extra", response_model=List[Dict[str, Any]])
async def get_extra_products(
    q: str = "", 
    restaurant_id: uuid.UUID = Query(None),
    db: AsyncSession = Depends(get_session)
):
    """
    Returns a list of products for manual ordering. Allows search by name.
    """
    excluded_categories = ['Ingredient', 'Vegetables', 'Meat', 'Sauces']
    
    from src.db.models.product import StockBalance
    
    # Left join with StockBalance if restaurant_id is provided
    if restaurant_id:
        stmt = (
            select(
                Product.id,
                Product.name_ru,
                Product.name_vn,
                Product.unit,
                Product.category,
                func.coalesce(StockBalance.amount, 0).label("stock")
            )
            .outerjoin(
                StockBalance, 
                (StockBalance.product_id == Product.id) & (StockBalance.restaurant_id == restaurant_id)
            )
        )
    else:
        stmt = select(Product)
    
    # If search query is provided, use it. Otherwise, filter out known food categories.
    if q:
        stmt = stmt.where(Product.name_ru.ilike(f"%{q}%"))
    else:
        stmt = stmt.where(
            (Product.category.notin_(excluded_categories)) | (Product.category.is_(None))
        )
        
    stmt = stmt.order_by(Product.name_ru).limit(50)
    
    result = await db.execute(stmt)
    # Use mappings() to avoid AttributeError: id when row format differs
    rows = result.mappings().all()
    
    return [
        {
            "product_id": str(r["id"]),
            "product_name": r["name_ru"],
            "product_name_vn": r["name_vn"] or "",
            "unit": r["unit"] or "шт",
            "category": r["category"] or "Uncategorized",
            "stock": float(r["stock"]) if "stock" in r else 0.0
        }
        for r in rows
    ]
