import asyncio
from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models.analytics import Anomalies

async def inspect():
    async with async_session_maker() as session:
        result = await session.execute(select(Anomalies))
        anomalies = result.scalars().all()
        print(f"Total Anomalies: {len(anomalies)}")
        for a in anomalies:
            print(f"Order: {a.order_id}, Product: {a.product_id}, Auto: {a.auto_qty}, Manual: {a.manual_qty}")

if __name__ == "__main__":
    asyncio.run(inspect())
