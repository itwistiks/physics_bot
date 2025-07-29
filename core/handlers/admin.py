from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message

from sqlalchemy import select, func

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


@router.message(Command("test_transaction"))
async def test_transaction(message: Message):
    """Тест транзакций"""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                count = await session.scalar(select(func.count(Task.id)))
                await message.answer(f"Всего задач: {count}")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
