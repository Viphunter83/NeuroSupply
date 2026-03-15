
import asyncio
import uuid
import logging
from datetime import date
from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models import Restaurant, SalesPlan
from src.services.data_loader.sales_plan_parser import SalesPlanParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the current Excel export from Google Sheets
PLAN_FILE = "data_samples/google_export.xlsx"

async def migrate():
    logger.info("Starting Sales Plan migration from Google Sheets to DB...")
    
    async with async_session_maker() as session:
        # Get all restaurants
        res = await session.execute(select(Restaurant))
        restaurants = res.scalars().all()
        
        if not restaurants:
            logger.error("No restaurants found in DB. Ingest restaurants first.")
            return

        parser = SalesPlanParser(PLAN_FILE)
        
        # We'll migrate for Jan 2026, Feb 2026, etc. if available
        # For now, let's do Jan 2026 as per the sample file
        year, month = 2026, 1
        
        total_inserted = 0
        for rest in restaurants:
            # We need a mapping from restaurant name to code (ANG, etc.)
            # For now, we'll try to find any code that matches the name or use common ones
            # In a real scenario, this would be a config or part of Restaurant model
            
            # Simple heuristic mapping for demo:
            code_map = {
                "ANG": "ANG",
                "VDNH": "VDNH",
                "DNL": "DNL"
            }
            # Try to find a code for this restaurant
            r_code = None
            for key in code_map:
                if key.lower() in rest.name.lower():
                    r_code = code_map[key]
                    break
            
            if not r_code:
                # If no code matched, try matching by the first part of the name
                r_code = rest.name.split()[0]
                
            logger.info(f"Parsing plans for {rest.name} (Code: {r_code})...")
            plans = parser.parse(rest.id, year, month, restaurant_code=r_code)
            
            if plans:
                for p_data in plans:
                    # Check if already exists
                    existing = await session.execute(
                        select(SalesPlan).where(
                            SalesPlan.restaurant_id == rest.id,
                            SalesPlan.date == p_data['date']
                        )
                    )
                    if not existing.scalar_one_or_none():
                        sp = SalesPlan(**p_data)
                        session.add(sp)
                        total_inserted += 1
        
        await session.commit()
        logger.info(f"Migration complete. Inserted {total_inserted} records.")

if __name__ == "__main__":
    asyncio.run(migrate())
