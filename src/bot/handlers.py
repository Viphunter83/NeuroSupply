from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from src.core.config import settings

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    webapp_url = settings.WEBAPP_URL or "https://google.com" # Fallback if not set
    kb = [
        [types.KeyboardButton(text="Open NeuroSupply", web_app=WebAppInfo(url=webapp_url))]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Welcome to NeuroSupply! Click below to open.", reply_markup=keyboard)
