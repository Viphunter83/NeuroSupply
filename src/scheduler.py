
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
import asyncio

# Import your tasks
from src.scripts.run_calc import run_calc
from src.scripts.sync_sheet_to_db import sync_all_restaurants

from src.services.notification import NotificationService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def sync_job_wrapper():
    """
    Syncs master data from Sheets at 04:00 AM.
    """
    logger.info(f"⏰ [Scheduler] Starting Sync Job at {datetime.now()}")
    try:
        await sync_all_restaurants()
        logger.info("✅ [Scheduler] Sync Job Completed")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Sync Job Failed: {e}", exc_info=True)

async def calc_job_wrapper():
    """
    Wraps the existing run_calc task to handle errors 
    and log execution.
    Runs at 06:00 AM.
    """
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
    """
    # 1. Sync Job: Every day at 04:00
    sync_trigger = CronTrigger(hour=4, minute=0)
    scheduler.add_job(
        sync_job_wrapper, 
        trigger=sync_trigger, 
        id="daily_sync", 
        replace_existing=True
    )
    
    # 2. Calculation Job: Every day at 06:00
    calc_trigger = CronTrigger(hour=6, minute=0)
    scheduler.add_job(
        calc_job_wrapper, 
        trigger=calc_trigger, 
        id="daily_calc", 
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🚀 Scheduler started. Jobs: [daily_sync at 04:00, daily_calc at 06:00]")

def shutdown_scheduler():
    logger.info("🛑 Stopping Scheduler...")
    scheduler.shutdown()
