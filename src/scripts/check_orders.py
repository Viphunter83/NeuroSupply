
import asyncio
from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models import Order, OrderStatus
from src.core.config import settings

async def check_orders():
    print(f"Checking Orders in DB...")
    async with async_session_maker() as session:
        stmt = select(Order)
        result = await session.execute(stmt)
        orders = result.scalars().all()
        
        print(f"Total Orders: {len(orders)}")
        for o in orders:
            print(f"Order ID: {o.id}, Status: {o.status}, Items: {len(o.items)}")
            if o.items:
                print(f"First Item: {o.items[0]}")

if __name__ == "__main__":
    asyncio.run(check_orders())
