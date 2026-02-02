
import logging
import asyncio
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import async_session_maker
from src.db.models import User, Restaurant
from src.services.calculation.engine_v2 import CalculationEngineV2
from aiogram import Bot, types
from aiogram.types import WebAppInfo

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.bot = Bot(token=self.bot_token) if self.bot_token else None

    async def send_daily_report_to_all(self, restaurant_id: Optional[str] = None):
        """
        Sends daily report to all registered users (COOK/MANAGER).
        """
        if not self.bot:
            logger.warning("NotificationService: No bot token. Skipping.")
            return

        async with async_session_maker() as db:
            # 1. Fetch Users
            stmt = select(User)
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            if not users:
                logger.info("No users to notify.")
                return

            # 2. Generate Report Content (Dry Run Calculation)
            # Fetch Rest ID
            if not restaurant_id:
                restaurant_id = settings.IIKO_ORG_ID # Default
            
            # Simple Text Generation (similar to /report logic)
            # In production, this should be refactored to a shared helper
            report_text = await self._generate_report_text(db, restaurant_id)
            
            if not report_text:
                return

            # 3. Send
            logger.info(f"Sending report to {len(users)} users...")
            
            base_url = settings.WEBAPP_URL or "http://localhost:5173"
            webapp_url = f"{base_url}?restaurant_id={restaurant_id}"
            kb = [[types.InlineKeyboardButton(text="Open Dashboard 🚀", web_app=WebAppInfo(url=webapp_url))]]
            markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
            
            for user in users:
                try:
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=report_text,
                        parse_mode="HTML",
                        reply_markup=markup
                    )
                except Exception as e:
                    logger.error(f"Failed to send to user {user.telegram_id}: {e}")
            
            # Close bot session
            await self.bot.session.close()

    async def _generate_report_text(self, db: AsyncSession, iiko_id: str) -> str:
        try:
            stmt = select(Restaurant).where(Restaurant.iiko_id == iiko_id)
            res = await db.execute(stmt)
            restaurant = res.scalar_one_or_none()
            if not restaurant:
                return "Error: Restaurant not found."
            
            # TODO: Use Real Plan Amount
            plan_amount = 50000.0 
            
            engine = CalculationEngineV2(db)
            results = await engine.calculate_needs(restaurant.id, plan_amount)
            
            total_items = sum(r['quantity'] for r in results)
            
            return (
                f"<b>🌅 Daily Forecast Ready!</b>\n"
                f"Restaurant: {restaurant.name}\n"
                f"Target Plan: {plan_amount:,.0f} ₽\n\n"
                f"Items to Order: {len(results)}\n"
                f"Total Units: {total_items}\n\n"
                f"<i>Please review the Prep Plan in the Dashboard.</i>"
            )
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return None
