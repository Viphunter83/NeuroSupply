
import asyncio
import os
import sys
import logging
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession 

# Add src to path
sys.path.append(os.getcwd())

from src.core.config import settings
from src.db.models import Restaurant, Order, ProductMix
from src.services.order_service import OrderService
from src.db.session import async_session_maker

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifySettings")

async def run_verification():
    """
    Verifies that OrderService fetches settings from Sheets and passes them to Engine.
    """
    logger.info("Starting Verification: Settings Flow")
    
    # Mock SheetsClient
    with patch("src.services.order_service.SheetsClient") as MockClient:
        mock_instance = MockClient.return_value
        
        # Mock fetch_settings return value
        # Let's say user set Safety Stock to 1.5 in the sheet
        mock_instance.fetch_settings.return_value = {
            "safety_stock": 1.5,
            "days_in_transit": 2,
            "active_restaurant_id": "some-id"
        }
        
        # Database Setup
        async with async_session_maker() as db:
            # 1. Create Test Data
            logger.info("1. Creating Test Data...")
            r_id = uuid.uuid4()
            rest = Restaurant(
                id=r_id, 
                iiko_id=uuid.uuid4(), 
                name="Settings Test Rest", 
                spreadsheet_id="mock_settings_sheet"
            )
            db.add(rest)
            await db.commit()
            
            try:
                # 2. Run Order Generation
                logger.info("2. Generating Order with Dynamic Settings...")
                service = OrderService(db)
                
                # Mock Engine 
                # We want to verify verify calculate_needs is called with ss=1.5
                service.engine = MagicMock()
                # Async mock for the method
                service.engine.calculate_needs = AsyncMock(return_value=([], []))
                
                await service.generate_draft_order(r_id, 10000.0)
                
                # 3. Verify
                logger.info("3. Verifying Inter-Service Calls...")
                
                # Check SheetsClient init
                MockClient.assert_called_with("mock_settings_sheet")
                
                # Check fetch_settings called
                mock_instance.fetch_settings.assert_called_once()
                
                # Check Engine call arguments
                service.engine.calculate_needs.assert_called_once()
                args, kwargs = service.engine.calculate_needs.call_args
                
                # Verify args
                # calculate_needs(restaurant_id, sales_plan_rub, safety_stock=ss, days_in_transit=dit)
                # First 2 are positional
                assert args[0] == r_id
                assert args[1] == 10000.0
                
                # Kwargs
                assert kwargs["safety_stock"] == 1.5
                assert kwargs["days_in_transit"] == 2
                
                logger.info("✅ Verification SUCCESS: Settings (1.5x, 2 days) passed to Engine correctly.")
                
            except Exception as e:
                logger.error(f"❌ Verification FAILED: {e}")
                raise e
            finally:
                # Cleanup
                logger.info("Cleaning up...")
                # Delete orders first
                from sqlalchemy import delete
                await db.execute(delete(Order).where(Order.restaurant_id == r_id))
                await db.commit()
                
                # Delete restaurant
                await db.delete(rest)
                await db.commit()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_verification())
