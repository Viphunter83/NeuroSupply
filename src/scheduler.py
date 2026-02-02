
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
import asyncio

# Import your task
from src.scripts.run_calc import run_calc

from src.services.notification import NotificationService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def job_wrapper():
    """
    Wraps the existing run_calc task to handle errors 
    and log execution.
    """
    logger.info(f"⏰ [Scheduler] Starting Daily Job at {datetime.now()}")
    try:
        await run_calc()
        logger.info("✅ [Scheduler] Daily Job Completed Successfully")
        
        # Notify Users
        notifier = NotificationService()
        await notifier.send_daily_report_to_all()
        logger.info("🔔 [Scheduler] Notifications Sent")
        
    except Exception as e:
        logger.error(f"❌ [Scheduler] Job Failed: {e}", exc_info=True)

def start_scheduler():
    """
    Configures and starts the scheduler.
    """
    # Schedule logic: Every day at 06:00
    trigger = CronTrigger(hour=6, minute=0)
    
    # Add Job
    scheduler.add_job(
        job_wrapper, 
        trigger=trigger, 
        id="daily_calc", 
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🚀 Scheduler started. Jobs configured: ['daily_calc' at 06:00]")

def shutdown_scheduler():
    logger.info("🛑 Stopping Scheduler...")
    scheduler.shutdown()
