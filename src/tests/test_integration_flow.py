
import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import date

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.services.order_service import OrderService
from src.db.models import Order, OrderStatus, Restaurant, Product
from src.db.models.analytics import Anomalies

# Mocks
RESTAURANT_ID = uuid.uuid4()
PRODUCT_ID = uuid.uuid4()

@pytest.mark.asyncio
async def test_order_anomaly_flow():
    # 1. Setup Mock DB Session
    mock_session = AsyncMock()
    
    # 2. Existing Draft Order
    initial_items = [
        {"product_id": str(PRODUCT_ID), "quantity": 10.0, "predicted_usage": 10.0, "product_name": "Test Product"}
    ]
    
    draft_order = Order(
        id=uuid.uuid4(),
        restaurant_id=RESTAURANT_ID,
        status=OrderStatus.DRAFT,
        items=initial_items
    )
    
    # Mock Select Order and Product
    async def mock_execute(stmt):
        mock_res = MagicMock()
        sql = str(stmt).lower()
        if "orders" in sql:
             mock_res.scalar_one_or_none.return_value = draft_order
        elif "products" in sql:
             # Return a list with one product that has our PRODUCT_ID
             test_product = Product(id=PRODUCT_ID, name_ru="Test Product", package_size=1.0)
             mock_res.scalars.return_value.all.return_value = [test_product]
        return mock_res
    
    mock_session.execute = AsyncMock(side_effect=mock_execute)
    
    # 3. Update with diff quantity to trigger anomaly
    service = OrderService(mock_session)
    
    # New items: Quantity changed 10 -> 15. Manual reason provided.
    new_items = [
        {"product_id": str(PRODUCT_ID), "quantity": 15.0, "reason": "Cook added extra"}
    ]
    
    await service.update_order_items(draft_order.id, new_items)
    
    # 4. Verify Anomaly Added
    # We check if session.add was called with an Anomalies object
    assert mock_session.add.call_count > 0
    
    # Find the anomaly call
    anomaly_call = None
    for call in mock_session.add.call_args_list:
        arg = call[0][0]
        if isinstance(arg, Anomalies):
            anomaly_call = arg
            break
            
    assert anomaly_call is not None
    assert anomaly_call.order_id == draft_order.id
    assert str(anomaly_call.product_id) == str(PRODUCT_ID)
    assert anomaly_call.auto_qty == 10.0
    assert anomaly_call.manual_qty == 15.0
    assert anomaly_call.reason == "Cook added extra"
    
    print("Anomaly Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_order_anomaly_flow())
