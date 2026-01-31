
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.db.session import async_session_maker
from src.services.iiko.client import IikoClient
from src.services.calculation.engine import CalculationEngine
from src.core.config import settings

async def main():
    print("--- Verifying Calculation Engine ---")
    iiko = IikoClient()
    await iiko.auth()
    
    async with async_session_maker() as session:
        engine = CalculationEngine(iiko, session)
        org_id = settings.IIKO_ORG_ID
        
        print(f"Calculating for Org: {org_id}")
        results = await engine.calculate_order(org_id)
        
        print("\nResults:")
        for item in results:
            print(f"- {item['product_name']}: {item['order_qty']} {item['unit']} (Forecast: {item['predicted_kg']:.2f})")
            
    await iiko.close()

if __name__ == "__main__":
    asyncio.run(main())
