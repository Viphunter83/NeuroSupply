
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import date, timedelta
from uuid import uuid4

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.services.calculation.engine import CalculationEngine
from src.services.iiko.client import IikoClient
from src.db.models import SalesPlan, Product, Restaurant, TechCard

# Mock Data
MOCK_ORG_ID = str(uuid4())
PRODUCT_ID_BUN = uuid4()
DISH_ID_BURGER = uuid4()
IIKO_DISH_ID_BURGER = uuid4()
IIKO_PRODUCT_ID_BUN = uuid4()

@pytest.mark.asyncio
async def test_calculation_engine_logic():
    # 1. Mock IikoClient
    mock_iiko = MagicMock(spec=IikoClient)
    
    # Mock Sales OLAP (Total 1000 RUB sales, 1 item sold)
    mock_iiko.get_sales_olap = AsyncMock(return_value={
        "data": [
            {
                "DishAmountInt": 10.0,
                "DishDiscountSumInt": 1000.0,
                "DishName": "Test Burger"
            }
        ]
    })
    
    # Mock Menu (Map DishName -> Dish ID iiko)
    mock_iiko.get_menu = AsyncMock(return_value={
        "products": [
            {
                "id": str(IIKO_DISH_ID_BURGER),
                "name": "Test Burger",
            }
        ]
    })
    
    # Mock Stock (0 stock)
    mock_iiko.get_stock_balances = AsyncMock(return_value=[])
    
    # 2. Mock DB Session
    mock_session = AsyncMock()
    
    # Mock Sales Plans (2 days, 5000 RUB each -> 10000 RUB total)
    sales_plans = [
        SalesPlan(date=date.today(), amount_rub=5000.0),
        SalesPlan(date=date.today() + timedelta(days=1), amount_rub=5000.0)
    ]
    
    # Mock TechCards
    # Dish "Test Burger" (IIKO_DISH_ID_BURGER) contains Bun (PRODUCT_ID_BUN) 0.1kg gross
    tech_cards = [
        TechCard(
            iiko_dish_id=IIKO_DISH_ID_BURGER,
            product_id=PRODUCT_ID_BUN,
            gross_amount=0.1
        )
    ]
    
    # Mock Products
    products = [
        Product(
            id=PRODUCT_ID_BUN,
            iiko_id=IIKO_PRODUCT_ID_BUN,
            name_ru="Bun",
            unit="pcs"
        )
    ]
    
    # Mocking session.execute behavior sequentially
    # The engine calls:
    # 1. _get_sales_plans
    # 2. _get_all_tech_cards
    # 3. _get_all_products
    
    # We define side_effect for execute
    async def mock_execute(stmt):
        mock_res = MagicMock()
        # We need to distinguish queries. 
        # Since stmt is an object, we can't easily check SQL string without compilation.
        # But we know the ORDER of calls in engine.py (V1 is sequential).
        # However, order might change.
        # Better heuristic: check the table being queried.
        
        # Checking str(stmt) usually contains table name
        sql = str(stmt)
        if "sales_plans" in sql:
            mock_res.scalars.return_value.all.return_value = sales_plans
        elif "tech_cards" in sql:
            mock_res.scalars.return_value.all.return_value = tech_cards
        elif "products" in sql:
            mock_res.scalars.return_value.all.return_value = products
        else:
             mock_res.scalars.return_value.all.return_value = []
             
        return mock_res

    mock_session.execute = AsyncMock(side_effect=mock_execute)

    # 3. Run Engine
    engine = CalculationEngine(mock_iiko, mock_session)
    results = await engine.calculate_order(MOCK_ORG_ID)
    
    # 4. Assertions
    # Calculation:
    # Consumption 7 days:
    # Burger Qty 10. TechCard Bun 0.1. -> Bun Usage = 1.0 kg (or pcs)
    # Sales 7 days: 1000 RUB.
    # Factor (Ratio): 1.0 / 1000 = 0.001 unit/RUB
    
    # Forecast:
    # Sales Plan: 10000 RUB.
    # Predicted Consumption = 10000 * 0.001 = 10.0 units.
    
    # Order:
    # Buffer = 1.2
    # Required = 10.0 * 1.2 - 0 (Stock) = 12.0
    # Rounding (pcs) -> ceil(12.0) = 12
    
    print("\nResults:", results)
    
    assert len(results) == 1
    item = results[0]
    assert item['product_name'] == "Bun"
    assert item['predicted_kg'] == 10.0
    assert item['order_qty'] == 12.0
    assert item['unit'] == "pcs" # From product

    print("Test passed!")

if __name__ == "__main__":
    asyncio.run(test_calculation_engine_logic())
