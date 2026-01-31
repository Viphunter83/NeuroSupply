
import logging
from typing import Optional, List
import uuid
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

from src.db.models import Order, OrderStatus, Restaurant
from src.schemas.order import OrderResponse

logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        from src.services.calculation.engine_v2 import CalculationEngineV2
        self.engine = CalculationEngineV2(db)

    async def export_order_to_excel(self, order_id: UUID) -> io.BytesIO:
        """
        Generates an Excel file for the order.
        Columns: "Код", "Наименование", "Ед. изм.", "Кол-во (План)", "Кол-во (Факт)", "Комментарий"
        """
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        wb = Workbook()
        ws = wb.active
        ws.title = f"Order {str(order_id)[:8]}"
        
        # Headers
        headers = ["Код", "Наименование", "Ед. изм.", "Кол-во (План)", "Кол-во (Факт)", "Комментарий"]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.border = Border(bottom=Side(style='thin'))

        # Data
        # items is a list of dicts.
        # Structure: product_id, product_name, unit, quantity (fact), predicted_usage (plan)
        
        for row_idx, item in enumerate(order.items, 2):
            # item is dict
            code = item.get('product_id', '') # Or iiko_id if available? Using internal ID for now or name
            name = item.get('product_name', 'Unknown')
            unit = item.get('unit', '')
            qty_plan = item.get('predicted_usage', 0)
            qty_fact = item.get('quantity', 0)
            
            ws.cell(row=row_idx, column=1, value=str(code))
            ws.cell(row=row_idx, column=2, value=name)
            ws.cell(row=row_idx, column=3, value=str(unit))
            ws.cell(row=row_idx, column=4, value=qty_plan)
            ws.cell(row=row_idx, column=5, value=qty_fact)
            ws.cell(row=row_idx, column=6, value="") # Comment
            
        # Adjust column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    async def get_latest_draft_order(self, restaurant_id: UUID) -> Optional[Order]:
        """
        Fetch the latest order with status DRAFT for a specific restaurant.
        """
        stmt = (
            select(Order)
            .where(
                Order.restaurant_id == restaurant_id,
                # In real app, we might also filter by status if we strictly want DRAFT
                 Order.status == OrderStatus.DRAFT
            )
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def confirm_order(self, order_id: UUID) -> Order:
        """
        Confirm an order by changing its status to VERIFIED_BY_COOK.
        """
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.DRAFT:
             # Depending on business logic, maybe allow re-confirming? 
             # For now, let's just log warning or allow it.
             logger.warning(f"Order {order_id} is already in state {order.status}")

        order.status = OrderStatus.VERIFIED_BY_COOK
        await self.db.commit()
        await self.db.refresh(order)
        
        logger.info(f"Order {order_id} confirmed (VERIFIED_BY_COOK).")
        return order

    async def generate_draft_order(self, restaurant_id: UUID, sales_plan_rub: float) -> Order:
        """
        Calculates needs and creates a new DRAFT order.
        """
        # 1. Calculate
        items = await self.engine.calculate_needs(restaurant_id, sales_plan_rub)
        
        # 2. Create Order
        new_order = Order(
            restaurant_id=restaurant_id,
            status=OrderStatus.DRAFT,
            items=items
        )
        self.db.add(new_order)
        await self.db.commit()
        await self.db.refresh(new_order)
        return new_order

    async def update_order_items(self, order_id: UUID, new_items: List[dict]) -> Order:
        """
        Updates order items and logs anomalies.
        """
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
             raise HTTPException(status_code=404, detail="Order not found")
             
        if order.status != OrderStatus.DRAFT:
             raise HTTPException(status_code=400, detail="Cannot update confirmed order")

        # Logic to detect anomalies (compare old vs new)
        # For simplicity, we just save the new items.
        # But we should log to Anomalies table if quantity differs significantly.
        # Let's map old items by product_id
        old_map = {item['product_id']: item for item in order.items}
        
        from src.db.models.analytics import Anomalies
        
        for new_item in new_items:
            p_id = new_item.get('product_id')
            new_qty = float(new_item.get('quantity', 0))
            old_item = old_map.get(p_id)
            
            if old_item:
                old_qty = float(old_item.get('quantity', 0))
                if abs(new_qty - old_qty) > 0.01:
                    # Anomaly detected
                    anomaly = Anomalies(
                        order_id=order.id,
                        product_id=uuid.UUID(p_id),
                        auto_qty=old_qty,
                        manual_qty=new_qty,
                        reason="Manual update via API"
                    )
                    self.db.add(anomaly)
            else:
                 # New item added?
                 pass

        order.items = new_items
        await self.db.commit()
        await self.db.refresh(order)
        return order
