from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import Bot

from sqlalchemy import select, func, text

from core.services.reminder_service import ReminderService, send_inactivity_reminders
from core.filters.admin import IsAdminFilter
from core.database.models import (
    User,
    UserStat,
    Topic,
    Task,
    UserProgress,
    UserAchievement,
    Achievement
)

from config.database import AsyncSessionLocal

import logging


logger = logging.getLogger(__name__)


router = Router()


@router.message(Command("users"), IsAdminFilter())
async def cmd_users(message: types.Message):
    async with AsyncSessionLocal() as session:
        users = await session.scalars(select(User))
        user_list = "\n".join(
            f"{user.id} | @{user.username or 'нет'} | {user.status.value}"
            for user in users
        )

    await message.answer(f"👥 Список пользователей:\n\n{user_list}")


@router.message(Command("simulate_inactivity"), IsAdminFilter())
async def simulate_inactivity(message: Message):
    from datetime import datetime, timedelta
    """Имитирует неактивность для теста"""
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        user.last_interaction_time = datetime.utcnow() - timedelta(hours=25)
        session.add(user)
        await session.commit()
    await message.answer("✅ Ваша последняя активность установлена 25 часов назад")


@router.message(Command("test_reminder"), IsAdminFilter())
async def test_reminder(message: types.Message, bot: Bot):  # Добавьте bot в параметры
    """Тест напоминаний"""
    try:
        await send_inactivity_reminders(bot)  # Передаем bot напрямую
        await message.answer("Напоминания отправлены")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
