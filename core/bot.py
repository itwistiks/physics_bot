from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config.settings import BOT_TOKEN

# Импорт только основных роутеров (без тестов)
from .handlers.common import router as start_router
from .handlers.reply_handlers import router as reply_router
from .handlers.inline_handlers import router as inline_router
from .handlers.admin import router as admin_router


# Регистрируем middleware
from core.middlewares.user_middleware import UserMiddleware

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


dp.update.middleware(UserMiddleware())


async def register_handlers():
    """Регистрация всех обработчиков"""
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(reply_router)
    dp.include_router(inline_router)
