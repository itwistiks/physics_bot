from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Text
from core.fsm.states import AdminStates
from aiogram.filters import StateFilter

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

from core.services.stats_service import reset_all_weekly_points

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


# @router.message(Command("simulate_inactivity"), IsAdminFilter())
# async def simulate_inactivity(message: Message):
#     from datetime import datetime, timedelta
#     """Имитирует неактивность для теста"""
#     async with AsyncSessionLocal() as session:
#         user = await session.get(User, message.from_user.id)
#         user.last_interaction_time = datetime.utcnow() - timedelta(hours=25)
#         session.add(user)
#         await session.commit()
#     await message.answer("✅ Ваша последняя активность установлена 25 часов назад")


@router.message(Command("test_reminder"), IsAdminFilter())
async def test_reminder(message: types.Message, bot: Bot):  # Добавьте bot в параметры
    """Тест напоминаний"""
    try:
        await send_inactivity_reminders(bot)  # Передаем bot напрямую
        await message.answer("Напоминания отправлены")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


@router.message(Command("send_reminders"), IsAdminFilter())
async def cmd_send_reminders(message: types.Message, bot: Bot):
    """Ручная отправка напоминаний всем пользователям"""
    try:
        service = ReminderService(bot)
        results = await service.send_reminders()

        await message.answer(
            "🔔 Напоминания отправлены:\n"
            f"• PROMO: {results.get('promo', 0)} пользователям\n"
            f"• INACTIVE: {results.get('inactive', 0)} пользователям\n\n"
            f"Следующая автоматическая проверка через {service.check_interval//3600} ч"
        )
    except Exception as e:
        logger.error(f"Error in send_reminders: {e}")
        await message.answer("⚠️ Ошибка при отправке напоминаний")


@router.message(Command("reset_weekly"), IsAdminFilter())
async def confirm_reset_weekly(message: types.Message, state: FSMContext):
    """Запрашивает подтверждение обнуления weekly points"""
    confirm_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, обнулить")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "⚠️ Вы уверены, что хотите обнулить weekly points всем пользователям?",
        reply_markup=confirm_kb
    )
    await state.set_state(AdminStates.CONFIRM_WEEKLY_RESET)


@router.message(
    Text("✅ Да, обнулить"),
    StateFilter(AdminStates.CONFIRM_WEEKLY_RESET),
    IsAdminFilter()
)
async def execute_reset_weekly(message: types.Message, state: FSMContext):
    """Выполняет обнуление weekly points после подтверждения"""
    async with AsyncSessionLocal() as session:
        try:
            count = await reset_all_weekly_points(session)
            await message.answer(
                f"♻️ Weekly points обнулены для {count} пользователей",
                reply_markup=types.ReplyKeyboardRemove()
            )
        except Exception as e:
            logger.error(f"Error in reset_weekly: {e}")
            await message.answer(
                "⚠️ Ошибка при обнулении weekly points",
                reply_markup=types.ReplyKeyboardRemove()
            )
        finally:
            await state.clear()


@router.message(
    Text("❌ Отмена"),
    StateFilter(AdminStates.CONFIRM_WEEKLY_RESET),
    IsAdminFilter()
)
async def cancel_reset_weekly(message: types.Message, state: FSMContext):
    """Отменяет операцию обнуления"""
    await message.answer(
        "❌ Обнуление weekly points отменено",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()


@router.message(Command("ahelp"), IsAdminFilter())
async def cmd_help(message: types.Message):
    help_text = """
/users - список пользователей
/test_reminder - тест напоминаний
/send_reminders - ручная отправка напоминаний всем пользователям
/reset_weekly - обнуляет weekly_points у всех пользователей
"""
    await message.answer(help_text, parse_mode="HTML")
