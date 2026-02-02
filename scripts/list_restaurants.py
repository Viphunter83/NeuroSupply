
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models import Restaurant

async def main():
    async with async_session_maker() as session:
        stmt = select(Restaurant)
        result = await session.execute(stmt)
        restaurants = result.scalars().all()
        
        print(f"Found {len(restaurants)} restaurants:")
        for r in restaurants:
            print(f"Name: {r.name}, ID: {r.id}, IikoID: {r.iiko_id}")

if __name__ == "__main__":
    asyncio.run(main())
