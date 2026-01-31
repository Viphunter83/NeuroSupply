import asyncio
import uuid
from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models.order import Order

async def inspect():
    async with async_session_maker() as session:
        result = await session.execute(select(Order))
        orders = result.scalars().all()
        print(f"Total Orders: {len(orders)}")
        for o in orders:
            print(f"Order: {o.id}, RestID: {o.restaurant_id}, Status: {o.status}")

if __name__ == "__main__":
    asyncio.run(inspect())
