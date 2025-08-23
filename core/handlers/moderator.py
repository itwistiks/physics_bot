from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta

from core.filters.admin import IsModeratorFilter
from core.database.models import User, UserProgress
from config.database import AsyncSessionLocal

router = Router()


@router.message(Command("active_users"), IsModeratorFilter())
async def cmd_active_users(message: types.Message):
    """Самые активные пользователи за последние 7 дней"""
    try:
        async with AsyncSessionLocal() as session:
            week_ago = datetime.now() - timedelta(days=7)

            # Пользователи с наибольшей активностью
            active_users = await session.execute(
                select(User, UserProgress.weekly_points)
                .join(UserProgress, User.id == UserProgress.user_id)
                .where(User.last_interaction_time >= week_ago)
                .order_by(desc(UserProgress.weekly_points))
                .limit(15)
            )

            if not active_users:
                await message.answer("📊 Нет активных пользователей за последнюю неделю")
                return

            result = ["🏆 Самые активные пользователи (неделя):\n"]
            for i, (user, weekly_points) in enumerate(active_users, 1):
                result.append(
                    f"{i}. @{user.username or 'Без username'} (ID: {user.id})\n"
                    f"   ⚡ XP за неделю: {weekly_points}\n"
                    f"   📅 Последняя активность: {user.last_interaction_time.strftime('%d.%m.%Y %H:%M')}"
                )

            # Разбиваем на сообщения если слишком длинное
            text = "\n".join(result)
            if len(text) > 4000:
                for i in range(0, len(text), 4000):
                    await message.answer(text[i:i+4000])
            else:
                await message.answer(text)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("top_users"), IsModeratorFilter())
async def cmd_top_users(message: types.Message):
    """Топ 10 пользователей по общему XP"""
    try:
        async with AsyncSessionLocal() as session:
            top_users = await session.execute(
                select(User, UserProgress.total_points)
                .join(UserProgress, User.id == UserProgress.user_id)
                .order_by(desc(UserProgress.total_points))
                .limit(10)
            )

            if not top_users:
                await message.answer("📊 Нет данных о пользователях")
                return

            result = ["🏆 Топ 10 пользователей по XP:\n"]
            for i, (user, total_points) in enumerate(top_users, 1):
                result.append(
                    f"{i}. @{user.username or 'Без username'} (ID: {user.id})\n"
                    f"   ⚡ Всего XP: {total_points}\n"
                    f"   🎯 Статус: {user.status.value}"
                )

            await message.answer("\n".join(result))

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("top_weekly_users"), IsModeratorFilter())
async def cmd_top_weekly_users(message: types.Message):
    """Топ 10 пользователей по XP за неделю"""
    try:
        async with AsyncSessionLocal() as session:
            top_users = await session.execute(
                select(User, UserProgress.weekly_points)
                .join(UserProgress, User.id == UserProgress.user_id)
                .order_by(desc(UserProgress.weekly_points))
                .limit(10)
            )

            if not top_users:
                await message.answer("📊 Нет данных за неделю")
                return

            result = ["🏆 Топ 10 пользователей за неделю:\n"]
            for i, (user, weekly_points) in enumerate(top_users, 1):
                result.append(
                    f"{i}. @{user.username or 'Без username'} (ID: {user.id})\n"
                    f"   ⚡ XP за неделю: {weekly_points}\n"
                    f"   🎯 Статус: {user.status.value}"
                )

            await message.answer("\n".join(result))

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("mhelp"), IsModeratorFilter())
async def cmd_mhelp(message: types.Message):
    """Помощь по командам модератора"""
    help_text = (
        "🔧 Команды модератора:\n\n"
        "📊 Статистика:\n"
        "/active_users - Самые активные пользователи\n"
        "/top_users - Топ 10 по общему XP\n"
        "/top_weekly_users - Топ 10 за неделю\n\n"

        "👨‍🏫 Команды преподавателя:\n"
        "/student_progress [@username] - Прогресс студента\n"
        "/send_feedback [@username] [message] - Отправить feedback\n"
    )
    await message.answer(help_text)
