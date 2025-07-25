from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config.settings import BOT_TOKEN

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Импорт обработчиков должен быть после создания dp


async def register_handlers():
    from core.handlers import start
    start.register(dp)
