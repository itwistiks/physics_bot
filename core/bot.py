from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config.settings import BOT_TOKEN

# Импорт только основных роутеров (без тестов)
from core.handlers.start import router as start_router
from core.handlers.reply_handlers import router as reply_router
from core.handlers.inline_handlers import router as inline_router

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


async def register_handlers():
    """Регистрация всех обработчиков"""
    dp.include_router(start_router)
    dp.include_router(reply_router)
    dp.include_router(inline_router)
