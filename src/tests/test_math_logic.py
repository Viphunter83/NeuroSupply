
import pytest
import asyncio
import uuid
import math
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.services.calculation.engine_v2 import CalculationEngineV2
from src.db.models import ProductMix, TechCard, Product, StockBalance, Order, OrderStatus
from src.core.config import settings

# Mock Data Constants
RESTAURANT_ID = uuid.uuid4()
DISH_ID = uuid.uuid4()
PRODUCT_ID = uuid.uuid4()

@pytest.mark.asyncio
async def test_engine_v2_math():
    # Setup Mocks
    mock_session = AsyncMock()
    
    # 1. Mock Data Objects
    
    # Mix: Probability 0.45 dishes per 1000 RUB
    mix = ProductMix(
        restaurant_id=RESTAURANT_ID,
        iiko_dish_id=str(DISH_ID),
        probability=0.45
    )
    
    # TechCard: 1.0 kg of Product per Dish
    tech_card = TechCard(
        iiko_dish_id=DISH_ID,
        product_id=PRODUCT_ID,
        gross_amount=1.0
    )
    
    # Product: Beef, Package 10kg
    product = Product(
        id=PRODUCT_ID,
        name_ru="Beef",
        name_vn="Thit Bo",
        unit="kg",
        package_size=10.0,
        package_unit="box"
    )
    
    # Stock Balance: 10kg
    stock = StockBalance(
        restaurant_id=RESTAURANT_ID,
        product_id=PRODUCT_ID,
        amount=10.0
    )
    
    # Transit Order: 5kg (Created 2h ago)
    # Note: Order items structure in logic: {'product_id': ..., 'quantity': ...}
    transit_order = Order(
        restaurant_id=RESTAURANT_ID,
        status=OrderStatus.VERIFIED_BY_COOK,
        created_at=datetime.utcnow() - timedelta(hours=2),
        items=[
            {'product_id': str(PRODUCT_ID), 'quantity': 5.0} # Assuming stored as KG in old logic
        ]
    )
    
    # Mock Session Execute Side Effects
    async def mock_execute(stmt):
        sql = str(stmt)
        mock_res = MagicMock()
        
        if "product_mix" in sql:
            mock_res.scalars.return_value.all.return_value = [mix]
        elif "tech_cards" in sql:
            mock_res.scalars.return_value.all.return_value = [tech_card]
        elif "products" in sql:
            mock_res.scalars.return_value.all.return_value = [product]
        elif "stock_balances" in sql:
            mock_res.scalars.return_value.all.return_value = [stock]
        elif "orders" in sql:
             # Transit query checks for VERIFIED orders
             mock_res.scalars.return_value.all.return_value = [transit_order]
        else:
            mock_res.scalars.return_value.all.return_value = []
            
        return mock_res

    mock_session.execute = AsyncMock(side_effect=mock_execute)

    # 2. Run Engine
    engine = CalculationEngineV2(mock_session)
    
    # Sales Plan: 100,000 RUB
    # Expected:
    # 1. Dish Qty = (100000 / 1000) * 0.45 = 45 dishes
    # 2. Raw Need = 45 * 1.0 = 45.0 kg
    # 3. With Safety (1.1) = 49.5 kg
    # 4. Minus Stock (10) = 39.5
    # 5. Minus Transit (5) = 34.5 kg
    # 6. Packaging (10kg/box) = ceil(34.5/10) = 4 boxes
    
    # Override settings just in case (though we hardcoded default)
    settings.SAFETY_STOCK_RATIO = 1.1
    
    results = await engine.calculate_needs(RESTAURANT_ID, 100000.0)
    
    # 3. Assertions
    assert len(results) == 1
    item = results[0]
    
    print("\nCalculation Result:", item)
    
    assert item['product_id'] == str(PRODUCT_ID)
    assert item['unit'] == "box"
    assert item['quantity'] == 4.0
    
    # Check extended info
    assert item['predicted_usage_kg'] == 45.0
    assert item['safety_usage_kg'] == 49.5
    assert item['stock_kg'] == 10.0
    assert item['transit_kg'] == 5.0

if __name__ == "__main__":
    asyncio.run(test_engine_v2_math())
