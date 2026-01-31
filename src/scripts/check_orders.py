import asyncio
import uuid
from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models import Order, OrderStatus

TEST_RESTAURANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

async def check_status():
    async with async_session_maker() as session:
        # Get all orders
        stmt = select(Order).where(Order.restaurant_id == TEST_RESTAURANT_ID).order_by(Order.created_at.desc())
        result = await session.execute(stmt)
        orders = result.scalars().all()
        
        print(f"Total Orders: {len(orders)}")
        for o in orders:
            print(f"ID: {o.id} | Status: {o.status} | Created: {o.created_at}")

if __name__ == "__main__":
    asyncio.run(check_status())
