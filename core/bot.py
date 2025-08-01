from core.middlewares.user_middleware import UserMiddleware
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config.settings import BOT_TOKEN

# Импорт только основных роутеров (без тестов)
from core.handlers.common import router as start_router
from core.handlers.reply_handlers import router as reply_router
from core.handlers.inline_handlers import router as inline_router
from core.handlers.admin import router as admin_router

# Напоминания
from core.utils.reminder_jobs import send_inactivity_reminders
from core.services.reminder_service import send_daily_reminders
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

# Регистрируем middleware

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


dp.update.middleware(UserMiddleware())


async def register_handlers():
    """Регистрация всех обработчиков"""
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(reply_router)
    dp.include_router(inline_router)


async def on_startup(bot: Bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_daily_reminders,
        'interval',  # 'cron' для конкретного времени
        hours=24,
        args=(bot,)
    )
    scheduler.start()


async def on_shutdown():
    scheduler.shutdown()

dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)
