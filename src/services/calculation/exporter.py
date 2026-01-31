
import pandas as pd
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class OrderExporter:
    def __init__(self, output_path: str = "draft_orders"):
        self.output_path = output_path
        
    def export_to_excel(self, order_list: List[Dict[str, Any]], filename: str = "Draft_Order.xlsx") -> str:
        """
        Exports the calculated order list to an Excel file.
        Returns the full path to the saved file.
        """
        try:
            df = pd.DataFrame(order_list)
            
            # Reorder/Rename columns for readability if needed
            # Current keys: ingredient_name, required_amount, unit, package_size, order_qty, order_unit, comment
            
            column_mapping = {
                "ingredient_name": "Ingredient",
                "required_amount": "Required (Raw)",
                "unit": "Unit",
                "package_size": "Pkg Size",
                "order_qty": "Order Qty",
                "order_unit": "Order Unit",
                "comment": "Comment / Calculation Logic"
            }
            
            df = df.rename(columns=column_mapping)
            
            # Ensure column order
            cols = ["Ingredient", "Required (Raw)", "Unit", "Pkg Size", "Order Qty", "Order Unit", "Comment / Calculation Logic"]
            df = df[cols]
            
            full_path = f"{self.output_path}/{filename}"
            
            # Ensure directory exists
            import os
            os.makedirs(self.output_path, exist_ok=True)
            
            df.to_excel(full_path, index=False)
            logger.info(f"Exported order to: {full_path}")
            return full_path
            
        except Exception as e:
            logger.error(f"Failed to export Excel: {e}")
            raise
