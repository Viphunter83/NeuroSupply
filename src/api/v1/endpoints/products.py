from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from src.api.deps import get_session
from src.db.models.product import Product

router = APIRouter()

@router.get("/extra", response_model=List[Dict[str, Any]])
async def get_extra_products(q: str = "", db: AsyncSession = Depends(get_session)):
    """
    Returns a list of products for manual ordering. Allows search by name.
    """
    excluded_categories = ['Ingredient', 'Vegetables', 'Meat', 'Sauces']
    
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
    products = result.scalars().all()
    
    return [
        {
            "product_id": str(p.id),
            "product_name": p.name_ru,
            "product_name_vn": p.name_vn or "",
            "unit": p.unit or "шт",
            "category": p.category or "Uncategorized",
        }
        for p in products
    ]
