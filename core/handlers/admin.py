from aiogram import Router, types, Bot
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
    """Список всех пользователей"""
    async with AsyncSessionLocal() as session:
        users = await session.scalars(
            select(User).order_by(User.registration_date.desc())
        )

        user_list = []
        for user in users:
            status_emoji = {
                'no_sub': '🔴', 'sub': '🟢', 'pro_sub': '🔵',
                'teacher': '👨‍🏫', 'moderator': '🔧', 'admin': '⚡'
            }.get(user.status.value, '⚪')

            user_list.append(
                f"{status_emoji} {user.id} | @{user.username or 'нет'} | "
                f"{user.status.value} | {user.registration_date.strftime('%d.%m.%Y')}"
            )

        # Разбиваем на сообщения по 20 пользователей
        for i in range(0, len(user_list), 20):
            await message.answer("\n".join(user_list[i:i+20]))


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


@router.message(Command("broadcast"), IsAdminFilter())
async def cmd_broadcast(message: types.Message, bot: Bot):  # Правильный тип
    """Массовая рассылка сообщения всем пользователям"""
    try:
        # Извлекаем текст рассылки
        if len(message.text.split()) < 2:
            await message.answer("❌ Использование: /broadcast <текст сообщения>")
            return

        broadcast_text = message.text.split(' ', 1)[1]

        async with AsyncSessionLocal() as session:
            # Получаем всех пользователей
            users = await session.scalars(select(User))

            success = 0
            failed = 0
            failed_users = []

            # Отправляем сообщение каждому пользователю
            for user in users:
                try:
                    await bot.send_message(
                        user.id,
                        f"📢 Сообщение от администратора:\n\n{broadcast_text}"
                    )
                    success += 1
                except Exception as e:
                    failed += 1
                    failed_users.append(
                        f"{user.id} (@{user.username or 'нет'})")
                    # Логируем ошибку для диагностики
                    print(
                        f"Не удалось отправить пользователю {user.id}: {str(e)}")

            # Формируем отчет
            report = (
                f"✅ Рассылка завершена:\n"
                f"✔️ Успешно: {success}\n"
                f"❌ Не удалось: {failed}"
            )

            # Добавляем список неудавшихся, если их немного
            if failed_users and len(failed_users) <= 10:
                report += f"\n\nНе удалось отправить:\n" + \
                    "\n".join(failed_users[:10])
            elif failed > 0:
                report += f"\n\nНе удалось отправить {failed} пользователям"

            await message.answer(report)

    except Exception as e:
        await message.answer(f"❌ Ошибка при рассылке: {str(e)}")


@router.message(Command("ahelp"), IsAdminFilter())
async def cmd_help(message: types.Message):
    help_text = """
⚡ Команды Админа:
/users - список пользователей
/test_reminder - тест напоминаний
/send_reminders - ручная отправка напоминаний всем пользователям
/reset_weekly - обнуляет weekly_points у всех пользователей
/broadcast [сообщение] - массовая рассылка сообщения

🔧 Команды модератора:
/active_users - Самые активные пользователи
/top_users - Топ 10 по общему XP
/top_weekly_users - Топ 10 за неделю

👨‍🏫 Команды преподавателя:
/student_progress [@username] - Прогресс студента
/send_feedback [@username] [message] - Отправить feedback
"""
    await message.answer(help_text, parse_mode="HTML")
