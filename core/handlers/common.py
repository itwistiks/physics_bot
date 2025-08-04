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


# @router.message(~Command(commands=["start", "help"]))
# async def handle_non_command(message: types.Message):
#     await message.answer(
#         "👋 Привет! Я бот для подготовки к ОГЭ по физике.\n"
#         "Нажми /start чтобы начать или /help для списка команд.\n\n"
#         "Я помогу:\n"
#         "✅ Решать задачи разных типов\n"
#         "✅ Изучать теорию\n"
#         "✅ Следить за прогрессом\n"
#         "✅ Готовиться к экзамену системно"
#     )


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
            logger.debug(f"Неудалось удалить сообщение: {e}")

    if task_message_id:
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=task_message_id
            )
        except Exception as e:
            # Сообщение могло быть уже удалено или не найдено
            logger.debug(f"Неудалось удалить сообщение: {e}")

    async with AsyncSessionLocal() as session:
        # Получаем или создаем пользователя
        user = await get_or_create_user(
            session=session,
            user_id=message.from_user.id,
            username=message.from_user.username
        )

    await message.answer(
        "📚 Привет! Я помогу подготовиться к ОГЭ по физике на 5! \nВыбери действие",
        reply_markup=main_menu_kb()
    )


# Добавьте в core/handlers/common.py
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
📚 <b>Помощь по боту</b>:

/start - Начать работу с ботом

<b>Основные функции</b>:
✏️ Практика - Решение задач по темам
📊 Статистика - Ваш прогресс и достижения
📖 Теория - Теоретические материалы

<b>Типы заданий</b>:
📋 Первая часть - Задания с выбором ответа
📘 Вторая часть - Задания с развернутым ответом
🔥 Сложные задачи - Задания повышенной сложности

По всем вопросам/предложениям доступна ✉️ Поддержка
"""
    await message.answer(help_text, parse_mode="HTML")
