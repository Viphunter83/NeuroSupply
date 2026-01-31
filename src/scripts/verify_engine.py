
import asyncio
import logging
import uuid
from sqlalchemy import select
from src.db.session import async_session_maker
from src.services.calculation.engine import CalculationEngine
from src.db.models import Restaurant

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("--- Verifying Calculation Engine ---")
    
    # Needs a valid restaurant ID from DB.
    # We seeded "VDNH" with iiko_id 7ed...
    iiko_org_id = uuid.UUID("7ed864a1-aa78-40dc-a9a1-585df1dfb2ca")
    
    async with async_session_maker() as session:
        # Lookup DB ID
        stmt = select(Restaurant).where(Restaurant.iiko_id == iiko_org_id)
        result = await session.execute(stmt)
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            print(f"Restaurant with Iiko ID {iiko_org_id} NOT FOUND in DB.")
            return

        print(f"Calculating for Org: {restaurant.name} (DB ID: {restaurant.id})")
        
        from src.services.iiko.client import IikoClient
        iiko_client = IikoClient()
        engine = CalculationEngine(iiko_client=iiko_client, db=session)
        results = await engine.calculate_order(restaurant.id)
        await iiko_client.close()
        
        print("\nResults:")
        print(f"Order ID: {results.id}")
        print(f"Status: {results.status}")
        print(f"Items: {len(results.items)}")
        for item in results.items[:5]:
            print(f"- {item.product_name}: {item.quantity} {item.unit}")

if __name__ == "__main__":
    asyncio.run(main())
