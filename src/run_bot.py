
import asyncio
import logging
from aiogram import Bot, Dispatcher
from src.core.config import settings
from src.bot.handlers import router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set!")
        return

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    
    # Register routers
    dp.include_router(router)
    
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
