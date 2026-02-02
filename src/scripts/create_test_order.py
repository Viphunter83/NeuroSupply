
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from src.db.session import engine
from src.db.models import Order, OrderStatus
from src.core.config import settings

from sqlalchemy import text

async def create_test_order():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        async with session.begin():
            # Test Restaurant ID (must match what we put in Frontend)
            restaurant_id = uuid.UUID("f2c046ab-4068-4794-b6e1-e41045f9ea31")
            
            # Create a DRAFT order
            # We need some dummy items. Ideally we should query products first, 
            # but for now let's just make up some or rely on the fact that existing products have IDs?
            # Actually, Order items usually reference product_ids.
            # Let's check if we can fetch some products to be safe.
            
            # Simple raw query to get a few product IDs
            result = await session.execute(text("SELECT id, name_ru, unit FROM products LIMIT 5"))
            products = result.fetchall()
            
            if not products:
                print("No products found! Run load_initial_data.py first.")
                return

            items = []
            for p in products:
                items.append({
                    "product_id": str(p.id),
                    "product_name": p.name_ru,
                    "unit": p.unit,
                    "quantity": 10.0,
                    "predicted_usage": 5.0,
                    "stock": 2.0,
                    "image_url": None
                })
            
            new_order = Order(
                id=uuid.uuid4(),
                restaurant_id=restaurant_id,
                status=OrderStatus.DRAFT,
                created_at=datetime.now(timezone.utc),
                items=items
            )
            
            session.add(new_order)
            print(f"Created DRAFT order {new_order.id} with {len(items)} items.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_order())
