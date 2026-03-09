
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
import asyncio

# Import your tasks
from src.scripts.run_calc import run_calc
from src.scripts.sync_sheet_to_db import sync_all_restaurants
from src.scripts.sync_empirical_recipes import sync_empirical_recipes
from src.scripts.sync_sales_facts import sync_sales_facts
from src.scripts.sync_stock_balances import sync_stock_balances
from src.scripts.sync_products import sync_products

from src.services.notification import NotificationService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def sync_products_wrapper():
    """Syncs product nomenclature from iiko at 01:30 AM."""
    logger.info(f"⏰ [Scheduler] Starting Products Nomenclature Sync at {datetime.now()}")
    try:
        await sync_products()
        logger.info("✅ [Scheduler] Products Sync Completed")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Products Sync Failed: {e}", exc_info=True)

async def sync_sales_facts_wrapper():
    """Syncs daily sales facts from iiko OLAP at 02:00 AM."""
    logger.info(f"⏰ [Scheduler] Starting Sales Facts Sync at {datetime.now()}")
    try:
        await sync_sales_facts(days_back=1)
        logger.info("✅ [Scheduler] Sales Facts Sync Completed")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Sales Facts Sync Failed: {e}", exc_info=True)

async def sync_empirical_recipes_wrapper():
    """Syncs empirical recipes from iiko OLAP at 03:00 AM."""
    logger.info(f"⏰ [Scheduler] Starting Empirical Recipes Sync Job at {datetime.now()}")
    try:
        await sync_empirical_recipes()
        logger.info("✅ [Scheduler] Empirical Recipes Sync Completed")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Empirical Recipes Sync Failed: {e}", exc_info=True)

async def sync_job_wrapper():
    """Syncs master data from Sheets at 04:00 AM."""
    logger.info(f"⏰ [Scheduler] Starting Sync Job at {datetime.now()}")
    try:
        await sync_all_restaurants()
        logger.info("✅ [Scheduler] Sync Job Completed")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Sync Job Failed: {e}", exc_info=True)

async def sync_stock_balances_wrapper():
    """Syncs stock balances from iiko at 05:00 AM."""
    logger.info(f"⏰ [Scheduler] Starting Stock Balances Sync at {datetime.now()}")
    try:
        await sync_stock_balances()
        logger.info("✅ [Scheduler] Stock Balances Sync Completed")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Stock Balances Sync Failed: {e}", exc_info=True)

async def calc_job_wrapper():
    """Runs calculation + notifications at 06:00 AM."""
    logger.info(f"⏰ [Scheduler] Starting Calculation Job at {datetime.now()}")
    try:
        await run_calc()
        logger.info("✅ [Scheduler] Calculation Job Completed Successfully")
        
        # Notify Users
        notifier = NotificationService()
        await notifier.send_daily_report_to_all()
        logger.info("🔔 [Scheduler] Notifications Sent")
        
    except Exception as e:
        logger.error(f"❌ [Scheduler] Calculation Job Failed: {e}", exc_info=True)

def start_scheduler():
    """
    Configures and starts the scheduler.
    Pipeline: 02:00 sales → 03:00 recipes → 04:00 sheets → 05:00 stock → 06:00 calc
    """
    # 0. Products Nomenclature Job: Every day at 01:30
    scheduler.add_job(
        sync_products_wrapper, 
        trigger=CronTrigger(hour=1, minute=30), 
        id="daily_products", 
        replace_existing=True
    )

    # 1. Sales Facts Job: Every day at 02:00
    scheduler.add_job(
        sync_sales_facts_wrapper, 
        trigger=CronTrigger(hour=2, minute=0), 
        id="daily_sales_facts", 
        replace_existing=True
    )

    # 2. Empirical Recipes Job: Every day at 03:00
    scheduler.add_job(
        sync_empirical_recipes_wrapper, 
        trigger=CronTrigger(hour=3, minute=0), 
        id="daily_empirical", 
        replace_existing=True
    )

    # 3. Sync Job (Sheets): Every day at 04:00
    scheduler.add_job(
        sync_job_wrapper, 
        trigger=CronTrigger(hour=4, minute=0), 
        id="daily_sync", 
        replace_existing=True
    )

    # 4. Stock Balances Job: Every day at 05:00
    scheduler.add_job(
        sync_stock_balances_wrapper, 
        trigger=CronTrigger(hour=5, minute=0), 
        id="daily_stock_balances", 
        replace_existing=True
    )
    
    # 5. Calculation Job: Every day at 06:00
    scheduler.add_job(
        calc_job_wrapper, 
        trigger=CronTrigger(hour=6, minute=0), 
        id="daily_calc", 
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🚀 Scheduler started. Jobs: [01:30 products, 02:00 sales_facts, 03:00 recipes, 04:00 sync, 05:00 stock, 06:00 calc]")

def shutdown_scheduler():
    logger.info("🛑 Stopping Scheduler...")
    scheduler.shutdown()
