
import asyncio
import sys
import os
from pathlib import Path
from datetime import date, timedelta
from sqlalchemy import select

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.db.session import async_session_maker
from src.db.models import SalesPlan, Restaurant
from src.core.config import settings

async def main():
    print("Seeding Sales Plans...")
    async with async_session_maker() as session:
        # 1. Get or Create Restaurant
        stmt = select(Restaurant).limit(1)
        result = await session.execute(stmt)
        restaurant = result.scalar_one_or_none()
        
        org_id = settings.IIKO_ORG_ID
        if not org_id:
            print("Error: IIKO_ORG_ID not set.")
            return

        if not restaurant:
            print(f"Creating restaurant with ID {org_id}")
            restaurant = Restaurant(id=org_id, iiko_id=org_id, name="VDNH Test")
            session.add(restaurant)
            await session.commit()
            await session.refresh(restaurant)
        else:
            print(f"Using existing restaurant: {restaurant.name} ({restaurant.id})")
            
        # 2. Create Sales Plans
        today = date.today()
        dates = [today, today + timedelta(days=1), today + timedelta(days=2)]
        
        amounts = [45000.0, 50000.0, 55000.0] # Dummy sales plan
        
        for d, amt in zip(dates, amounts):
            # Check if exists
            stmt = select(SalesPlan).where(SalesPlan.date == d, SalesPlan.restaurant_id == restaurant.id)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            
            if existing:
                print(f"Plan for {d} exists: {existing.amount_rub}")
                existing.amount_rub = amt # Update
            else:
                print(f"Creating plan for {d}: {amt}")
                plan = SalesPlan(date=d, amount_rub=amt, restaurant_id=restaurant.id)
                session.add(plan)
        
        await session.commit()
        print("Done seeding.")

if __name__ == "__main__":
    asyncio.run(main())
