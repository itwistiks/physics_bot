from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import Bot

from sqlalchemy import select, func, text

from core.utils.reminder_jobs import get_reminder_text
from core.services.reminder_service import send_inactivity_reminders
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


# Пока нерабочая функция
# @router.message(Command("mystats"))
# async def cmd_show_stats(message: types.Message):
#     async with AsyncSessionLocal() as session:
#         # Получаем основную информацию о пользователе
#         user = await session.get(User, message.from_user.id)
#         if not user:
#             await message.answer("Пользователь не найден.")
#             return

#         # Получаем прогресс пользователя
#         progress = await session.get(UserProgress, message.from_user.id)

#         # Получаем общую статистику по темам
#         stats = await session.execute(
#             select(UserStat, Topic.title_ru)
#             .join(Topic, UserStat.topic_id == Topic.id)
#             .where(
#                 (UserStat.user_id == message.from_user.id) &
#                 # Только статистика по темам (без подтем)
#                 (UserStat.subtopic_id.is_(None))
#             )
#             .order_by(UserStat.percentage.desc())
#         )

#         # Получаем достижения пользователя
#         achievements = await session.execute(
#             select(UserAchievement, Achievement)
#             .join(Achievement, UserAchievement.achievement_id == Achievement.id)
#             .where(UserAchievement.user_id == message.from_user.id)
#         )

#         # Формируем текст ответа
#         response = [
#             f"📊 <b>Ваша статистика</b>",
#             f"",
#             f"👤 <b>Основная информация:</b>",
#             f"• Статус: {user.status.value}",
#             f"• Дата регистрации: {user.registration_date.strftime('%d.%m.%Y')}",
#             f"• Последняя активность: {user.last_interaction_time.strftime('%d.%m.%Y %H:%M')}",
#             f"",
#             f"📈 <b>Прогресс:</b>",
#             f"• Текущая серия: {progress.current_streak} дней",
#             f"• Всего очков: {progress.total_points}",
#             f"• Очков за неделю: {progress.weekly_points}",
#             f"• Дневной рекорд: {progress.daily_record} задач",
#             f"",
#             f"🏆 <b>Достижения:</b>"
#         ]

#         # Добавляем достижения
#         for ua, achievement in achievements:
#             if ua.unlocked_at:
#                 response.append(
#                     f"• {achievement.name} ✅ ({ua.unlocked_at.strftime('%d.%m.%Y')})")
#             else:
#                 response.append(f"• {achievement.name} - {ua.progress}%")

#         response.extend([
#             f"",
#             f"📚 <b>Статистика по темам:</b>"
#         ])

#         # Добавляем статистику по темам
#         for stat, topic_name in stats:
#             response.append(
#                 f"• {topic_name}: "
#                 f"{stat.correct_answers}/{stat.total_attempts} "
#                 f"({stat.percentage:.1f}%)"
#             )

#         await message.answer("\n".join(response), parse_mode="HTML")


@router.message(Command("test_transaction"), IsAdminFilter())
async def test_transaction(message: types.Message, bot: Bot):
    """Полноценный тест системы напоминаний"""
    try:
        async with AsyncSessionLocal() as session:
            # 1. Получаем тестовые данные
            reminder_text = await get_reminder_text(session, 'inactive')
            user = await session.get(User, message.from_user.id)

            # 2. Отправляем информационное сообщение
            await message.answer(
                f"🔧 Тест системы напоминаний\n"
                f"──────────────────────\n"
                f"ℹ️ Ваши данные:\n"
                f"ID: {user.id}\n"
                f"Username: @{user.username}\n"
                f"Статус: {user.status}\n"
                f"Последняя активность: {user.last_interaction_time}\n"
                f"──────────────────────\n"
                f"📝 Текст напоминания:\n{reminder_text}"
            )

            # 3. Имитируем реальное напоминание
            try:
                await bot.send_message(
                    chat_id=user.id,
                    text=f"🔔 Тестовое напоминание:\n\n{reminder_text}"
                )
                await message.answer("✅ Напоминание успешно отправлено!")
            except Exception as e:
                await message.answer(f"❌ Ошибка отправки: {str(e)}")

    except Exception as e:
        await message.answer(f"❌ Критическая ошибка: {str(e)}")
        logger.critical(f"Reminder test failed: {e}", exc_info=True)


@router.message(Command("simulate_inactivity"))
async def simulate_inactivity(message: Message):
    from datetime import datetime, timedelta
    """Имитирует неактивность для теста"""
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        user.last_interaction_time = datetime.utcnow() - timedelta(hours=25)
        session.add(user)
        await session.commit()
    await message.answer("✅ Ваша последняя активность установлена 25 часов назад")


@router.message(Command("test_reminder"))
async def test_reminder(message: types.Message, bot: Bot):  # Добавьте bot в параметры
    """Тест напоминаний"""
    try:
        await send_inactivity_reminders(bot)  # Передаем bot напрямую
        await message.answer("Напоминания отправлены")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
