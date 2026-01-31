
import random
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Product, SalesPlan

async def generate_mock_sales(session: AsyncSession, target_date: date, restaurant_id: str) -> list[dict]:
    """
    Generates synthetic sales data based on SalesPlan and Products in DB.
    Returns format compatible with Iiko SALES OLAP report:
    [
        {"DishName": "...", "DishAmountInt": ..., "DishDiscountSumInt": ...},
        ...
    ]
    """
    # 1. Get Sales Plan for date
    stmt = select(SalesPlan).where(SalesPlan.date == target_date, SalesPlan.restaurant_id == restaurant_id)
    result = await session.execute(stmt)
    plan = result.scalar_one_or_none()
    
    target_revenue = float(plan.amount_rub) if plan else 50000.0
    
    # Apply noise (-10% to +15%)
    noise = random.uniform(0.9, 1.15)
    actual_revenue = target_revenue * noise
    
    # 2. Get Products
    products_res = await session.execute(select(Product))
    products = products_res.scalars().all()
    
    if not products:
        return []

    # 3. Distribute Revenue
    # Heuristic: Pareto principle? Or random distribution.
    # Let's shuffle products and assign chunks.
    
    sales_data = []
    remaining_revenue = actual_revenue
    
    # Filter products that look like "Dishes" (have units like 'шт' or 'порция'?)
    # For now use all.
    
    random.shuffle(products)
    
    for i, product in enumerate(products):
        if remaining_revenue <= 0:
            break
            
        if i == len(products) - 1:
            revenue_share = remaining_revenue
        else:
            # Random share up to 5% of total per product
            max_share = actual_revenue * 0.05
            revenue_share = random.uniform(0, min(remaining_revenue, max_share))
        
        remaining_revenue -= revenue_share
        
        # Estimate price (random 100 - 1000 RUB)
        price = random.uniform(100, 1000)
        qty = max(1, int(revenue_share / price))
        revenue = qty * price
        
        sales_data.append({
            "DishName": product.name_ru,
            "DishAmountInt": float(qty),
            "DishDiscountSumInt": float(revenue)
        })
        
    return sales_data
