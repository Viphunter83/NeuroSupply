
import asyncio
import sys
import os
import uuid

sys.path.append(os.getcwd())

from src.db.session import async_session_maker
from src.db.models import Restaurant

async def main():
    async with async_session_maker() as session:
        # ARTL ID from logs: 7a416cbc-c318-4aaf-be58-4398e58a4b0d
        iiko_id = "7a416cbc-c318-4aaf-be58-4398e58a4b0d"
        name = "ARTL"
        
        # Check if exists
        from sqlalchemy import select
        stmt = select(Restaurant).where(Restaurant.iiko_id == iiko_id)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        
        if existing:
            print("Restaurant ARTL already exists.")
            return

        new_rest = Restaurant(
            id=uuid.uuid4(),
            iiko_id=iiko_id,
            name=name,
            settings={"time_zone": "Europe/Moscow"}
        )
        session.add(new_rest)
        await session.commit()
        print(f"Added Restaurant ARTL with iiko_id {iiko_id}")

if __name__ == "__main__":
    asyncio.run(main())
