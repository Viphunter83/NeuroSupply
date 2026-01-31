
import asyncio
from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models import Product

async def check_products():
    print(f"Checking Products in DB...")
    async with async_session_maker() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        print(f"Total Products: {len(products)}")

if __name__ == "__main__":
    asyncio.run(check_products())
