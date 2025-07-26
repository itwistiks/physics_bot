# Импорт роутеров
from core.handlers.start import router as start_router
from core.handlers.db_test import router as db_test_router
from core.handlers.menu_handlers import router as menu_handlers

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config.settings import BOT_TOKEN

from core.handlers import routers


bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


# Обработчики


async def register_handlers():
    dp.include_router(start_router)
    dp.include_router(db_test_router)
    dp.include_router(menu_handlers)


async def register_handlers():
    for router in routers:
        dp.include_router(router)
