from aiogram import Router, types
from aiogram.filters import Command
from core.services.user_service import get_or_create_user
from config.database import AsyncSessionLocal
from core.keyboards.reply import main_menu_kb
from sqlalchemy import select


router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    async with AsyncSessionLocal() as session:
        # Получаем или создаем пользователя
        user = await get_or_create_user(
            session=session,
            user_id=message.from_user.id,
            username=message.from_user.username
        )

    await message.answer(
        "📚 Привет! Я помогу подготовиться к ОГЭ по физике на 5!",
        reply_markup=main_menu_kb()
    )
