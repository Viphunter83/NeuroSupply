
import sys
import os
import asyncio
import logging
import calendar
import uuid # Fixed missing import
from datetime import datetime, date

sys.path.append(os.getcwd())
from src.services.data_loader.sheets_client import SheetsClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONTH_MAP = {
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5, "июнь": 6,
    "июль": 7, "август": 8, "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12
}

WEEKDAY_MAP = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# Weight coefficients (Simple heuristic)
WEIGHTS = {
    0: 0.8, # Mon
    1: 0.9, # Tue
    2: 0.9, # Wed
    3: 1.0, # Thu
    4: 1.3, # Fri (High Traffic)
    5: 1.3, # Sat (High Traffic)
    6: 1.1  # Sun
}

async def main():
    logger.info("Starting Forecasting...")
    client = SheetsClient(settings.GOOGLE_SHEETS_SPREADSHEET_ID)
    
    # 1. Get Context
    rest_name = client.get_active_restaurant_name()
    logger.info(f"Active Restaurant: {rest_name}")

    # 2. Read Target
    # We pass the restaurant name so it tries to find the specific row (e.g. for ARTL)
    data = client.get_monthly_plan_target(restaurant_name=rest_name)
    month_str = data.get("month", "").lower().strip()
    target = data.get("target", 0.0)
    
    logger.info(f"Input for {rest_name}: Month='{month_str}', Target={target}")
    
    if not month_str or target <= 0:
        logger.warning(f"Invalid input (Target={target}). Initializing with defaults...")
        
        # Initialize headers with User's requested values (Tweaked to Feb for Demo)
        # Note: If separate rows are needed, user must add them manually for now as per logic,
        # or we just init the basic structure.
        client.update_worksheet("2. ПЛАН ПРОДАЖ 📅", [
            ["Месяц", "Ресторан", "Сумма Плана"],
            ["Февраль 2026", "Все", 2050219] 
        ])
        logger.info("Headers initialized. Re-fetching...")
        return # Stop here to let user fill it

    # 3. Parse Date
    try:
        parts = month_str.split()
        m_name = parts[0]
        year = int(parts[1]) if len(parts) > 1 else datetime.now().year
        month = MONTH_MAP.get(m_name, 1)
    except Exception as e:
        logger.error(f"Failed to parse date '{month_str}': {e}")
        return

    # 3. Generate Daily Breakdown
    num_days = calendar.monthrange(year, month)[1]
    days = []
    total_weight = 0.0
    
    for day in range(1, num_days + 1):
        dt = date(year, month, day)
        wd = dt.weekday()
        w = WEIGHTS.get(wd, 1.0)
        days.append({"date": dt, "weight": w, "wd_name": WEEKDAY_MAP[wd]})
        total_weight += w
        
    # 4. Distribute Target
    daily_rows = []
    cumulative = 0.0
    
    for i, d in enumerate(days):
        # Calculate share
        portion = target * (d["weight"] / total_weight)
        
        # Last day adjustment to match exact sum
        if i == len(days) - 1:
            portion = target - cumulative
            
        cumulative += portion
        
        # Row: Date, Weekday, Amount
        row = [
            d["date"].strftime("%d.%m.%Y"),
            d["wd_name"],
            round(portion, 2)
        ]
        daily_rows.append(row)

    # 5. Write to Sheets
    logger.info(f"Generated {len(daily_rows)} days. Updating Sheet...")
    client.update_daily_forecast(daily_rows)
    logger.info("Forecast Updated in Sheets!")

    # 6. Write to DB (Sync for API Fallback)
    logger.info("Syncing with DB...")
    
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import delete
    from src.db.session import engine
    from src.db.models import SalesPlan, Restaurant
    from sqlalchemy import select

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Resolve Restaurant ID
        # Sheets client gives us 'rest_name' but we need UUID.
        # Try to find by name or use active ID from sheets if possible
        
        # We can try to get ID via SheetsClient but it might check 'НАСТРОЙКИ'
        active_id_str = client.get_active_restaurant_id()
        
        stmt = select(Restaurant).where(Restaurant.iiko_id == active_id_str)
        res = await session.execute(stmt)
        restaurant = res.scalar_one_or_none()
        
        if not restaurant:
            # Fallback: find by name?
            # Or just warn
            logger.warning(f"Could not find restaurant with ID {active_id_str} in DB. Skipping DB sync.")
        else:
            logger.info(f"Syncing for Restaurant: {restaurant.name}")
            
            # Prepare objects
            db_objects = []
            dates_to_clear = []
            
            for d_row in daily_rows:
                # row: [DateStr, WdName, Amount]
                date_str = d_row[0]
                amount = d_row[2]
                
                dt_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
                dates_to_clear.append(dt_obj)
                
                sp = SalesPlan(
                    id=uuid.uuid4(),
                    restaurant_id=restaurant.id,
                    date=dt_obj,
                    amount_rub=amount
                )
                db_objects.append(sp)
            
            # Clear old plans for these dates
            if dates_to_clear:
                await session.execute(
                    delete(SalesPlan).where(
                        SalesPlan.restaurant_id == restaurant.id,
                        SalesPlan.date.in_(dates_to_clear)
                    )
                )
            
            # Insert new
            session.add_all(db_objects)
            await session.commit()
            logger.info(f"Saved {len(db_objects)} SalesPlan records to DB.")

if __name__ == "__main__":
    asyncio.run(main())
