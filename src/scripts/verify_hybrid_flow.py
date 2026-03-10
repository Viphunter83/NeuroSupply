
import asyncio
import os
import sys
import logging
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


# Add src to path
sys.path.append(os.getcwd())

from src.core.config import settings
from src.db.models import Restaurant, Order, ProductMix
from src.services.order_service import OrderService
from src.db.session import async_session_maker

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyHybrid")

async def run_verification():
    """
    Verifies that generating a draft order triggers the export to Google Sheets.
    """
    logger.info("Starting Verification: Hybrid Flow Export")
    
    # Mock SheetsClient
    with patch("src.services.order_service.SheetsClient") as MockClient:
        mock_instance = MockClient.return_value
        
        
        # Database Setup
        # Use existing session maker
        async with async_session_maker() as db:
            # 1. Create Test Data
            logger.info("1. Creating Test Data...")
            r_id = uuid.uuid4()
            rest = Restaurant(
                id=r_id, 
                iiko_id=uuid.uuid4(), 
                name="Test Export Rest", 
                spreadsheet_id="mock_sheet_id_123"
            )
            db.add(rest)
            await db.commit()
            
            # Add some product mix data for the engine to use
            dish_id = uuid.uuid4()
            mix = ProductMix(
                restaurant_id=r_id,
                iiko_dish_id="test-dish-1",
                probability=10.0 # High prob to ensure it gets picked
            )
            db.add(mix)
            await db.commit()
            
            try:
                # 2. Run Order Generation
                logger.info("2. Generating Draft Order...")
                service = OrderService(db)
                
                # Mock Engine calculation
                service.engine = MagicMock()
                mock_items = [{
                    "product_id": str(uuid.uuid4()),
                    "product_name": "Test Dish",
                    "quantity": 5,
                    "predicted_usage": 5,
                    "unit": "kg",
                    "comment": "Auto"
                }]
                mock_dishes = [{
                    "iiko_dish_id": "test-dish-1",
                    "quantity": 10,
                    "plan_revenue": 5000
                }]
                service.engine.calculate_needs = AsyncMock(return_value=(mock_items, mock_dishes))
                
                order = await service.generate_draft_order(r_id, 10000.0)
                
                logger.info(f"   Order Created: {order.id}")
                
                # 3. Verify Export Trigger
                logger.info("3. Verifying Sheet Export...")
                
                # Check if SheetsClient was initialized with correct ID
                MockClient.assert_called_with("mock_sheet_id_123")
        
                # Verify Draft Export
                mock_instance.write_draft_order.assert_called_once()
                args, _ = mock_instance.write_draft_order.call_args
                items_arg = args[0]
                assert len(items_arg) == 1
                assert items_arg[0]["product_name"] == "Test Dish"
                
                # Verify Dish Calc Export (New)
                mock_instance.write_dish_calculation.assert_called_once()
                d_args, _ = mock_instance.write_dish_calculation.call_args
                dishes_arg = d_args[0]
                assert len(dishes_arg) == 1
                assert dishes_arg[0]["iiko_dish_id"] == "test-dish-1"
                assert dishes_arg[0]["quantity"] > 0
                
                logger.info("   Exported Items Count: 1")
                logger.info("✅ Verification SUCCESS: Export triggered correctly.")
                
            finally:
                # Cleanup
                logger.info("Cleanup...")
                await db.execute(select(Order).where(Order.restaurant_id == r_id)) # scalar? no delete
                # ORM Delete
                await db.delete(order)
                await db.delete(mix)
                await db.delete(rest)
                await db.commit()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    # Need correct import for select/delete
    from sqlalchemy import select, delete
    
    asyncio.run(run_verification())
