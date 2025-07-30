from aiogram import Router, types, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from core.services.user_service import get_or_create_user
from config.database import AsyncSessionLocal
from core.keyboards.reply import main_menu_kb
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    task_message_id = data.get('task_message_id')

    if menu_message_id:
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=menu_message_id
            )
        except Exception as e:
            # Сообщение могло быть уже удалено или не найдено
            logger.debug(f"Не удалось удалить сообщение: {e}")

    if task_message_id:
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=task_message_id
            )
        except Exception as e:
            # Сообщение могло быть уже удалено или не найдено
            logger.debug(f"Не удалось удалить сообщение: {e}")

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
