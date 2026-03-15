import asyncio
import pandas as pd
import logging
import uuid
from datetime import datetime
from sqlalchemy import select, delete, and_
from src.db.session import async_session_maker
from src.db.models.analytics import SalesFact
from src.db.models.restaurant import Restaurant
from src.services.ml.forecast_service import ForecastService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def import_sales_report(file_path: str, restaurant_id: uuid.UUID, column_mapping: dict = None):
    """
    Imports sales data from an Excel/CSV file into SalesFact table.
    
    Expected column_mapping example:
    {
        'date': 'Дата',
        'dish_name': 'Наименование',
        'quantity': 'Кол-во',
        'revenue': 'Сумма'
    }
    """
    if not column_mapping:
        column_mapping = {
            'date': 'Дата',
            'dish_name': 'Наименование',
            'quantity': 'Кол-во',
            'revenue': 'Сумма'
        }

    logger.info(f"Loading file: {file_path}")
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)

    # Validate mapping
    for key, col in column_mapping.items():
        if col not in df.columns:
            logger.error(f"Column '{col}' not found in file. Available columns: {list(df.columns)}")
            return

    async with async_session_maker() as session:
        # Check restaurant
        res = await session.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
        restaurant = res.scalar_one_or_none()
        if not restaurant:
            logger.error(f"Restaurant {restaurant_id} not found.")
            return

        # Prepare records
        stats = {"inserted": 0, "errors": 0}
        
        # We might want to clear existing data for the dates found in the file to avoid duplicates
        dates_in_file = pd.to_datetime(df[column_mapping['date']]).dt.date.unique()
        
        for d in dates_in_file:
            await session.execute(
                delete(SalesFact).where(
                    and_(
                        SalesFact.restaurant_id == restaurant_id,
                        SalesFact.date == d
                    )
                )
            )

        for _, row in df.iterrows():
            try:
                # Parse date
                raw_date = row[column_mapping['date']]
                if isinstance(raw_date, str):
                    fact_date = pd.to_datetime(raw_date).date()
                else:
                    fact_date = raw_date.date() if hasattr(raw_date, 'date') else raw_date

                fact = SalesFact(
                    restaurant_id=restaurant_id,
                    iiko_dish_id=str(row[column_mapping['dish_name']]), # Using name as ID if real ID is missing
                    dish_name=str(row[column_mapping['dish_name']]),
                    date=fact_date,
                    quantity=float(row[column_mapping['quantity']]),
                    revenue_rub=float(row[column_mapping['revenue']])
                )
                session.add(fact)
                stats["inserted"] += 1
            except Exception as e:
                logger.warning(f"Failed to process row: {e}")
                stats["errors"] += 1

        await session.commit()
        logger.info(f"✅ Import completed for {restaurant.name}: {stats['inserted']} records inserted, {stats['errors']} errors.")
        
        # Retrain ML if enough data
        logger.info("Triggering ML training update...")
        ml_service = ForecastService()
        await ml_service.train_from_db(session)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python import_sales_report.py <path_to_file> <restaurant_uuid>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    rest_id = uuid.UUID(sys.argv[2])
    asyncio.run(import_sales_report(file_path, rest_id))
