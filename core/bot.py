from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config.settings import BOT_TOKEN
from core.utils.reminder_scheduler import ReminderScheduler

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
reminder_scheduler = None


async def register_handlers():
    """Регистрирует все обработчики команд"""
    from core.handlers.common import router as common_router
    from core.handlers.teacher import router as teacher_router
    from core.handlers.moderator import router as moderator_router
    from core.handlers.admin import router as admin_router
    from core.handlers.inline_handlers import router as inline_router
    from core.handlers.reply_handlers import router as reply_router

    dp.include_router(common_router)
    dp.include_router(teacher_router)
    dp.include_router(moderator_router)
    dp.include_router(admin_router)
    dp.include_router(inline_router)
    dp.include_router(reply_router)


async def on_startup():
    """Действия при запуске бота"""
    global reminder_scheduler
    reminder_scheduler = ReminderScheduler(bot)
    await reminder_scheduler.start()
    await register_handlers()


async def on_shutdown():
    """Действия при остановке бота"""
    if reminder_scheduler:
        await reminder_scheduler.stop()


def run_bot():
    """Запускает бота"""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.run_polling(bot)
