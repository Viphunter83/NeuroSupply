import asyncio
import logging
from aiogram import Bot, Dispatcher
from src.core.config import settings

logging.basicConfig(level=logging.INFO)

async def main():
    if not settings.BOT_TOKEN:
        logging.warning("BOT_TOKEN is not set. Bot will not start.")
        return

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    
    from src.bot.handlers import router
    dp.include_router(router)

    logging.info("Starting Telegram Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
