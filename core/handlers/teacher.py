from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from core.filters.admin import IsTeacherFilter
from core.database.models import User, UserStat, UserProgress
from config.database import AsyncSessionLocal

router = Router()


@router.message(Command("student_progress"), IsTeacherFilter())
async def cmd_student_progress(message: types.Message):
    """Прогресс конкретного студента по username"""
    try:
        # Извлекаем username из команды
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Использование: /student_progress @username")
            return

        # Убираем @ и приводим к нижнему регистру
        username_search = parts[1].lstrip('@').lower()

        async with AsyncSessionLocal() as session:
            # Ищем пользователя по части username
            users = await session.scalars(
                select(User).where(User.username.ilike(f"%{username_search}%"))
            )

            users_list = list(users)

            if not users_list:
                await message.answer("❌ Пользователь с таким username не найден")
                return

            if len(users_list) > 1:
                # Если найдено несколько пользователей
                user_list_text = "Найдено несколько пользователей:\n"
                for i, user in enumerate(users_list[:10], 1):
                    user_list_text += f"{i}. @{user.username} (ID: {user.id})\n"

                if len(users_list) > 10:
                    user_list_text += f"\n... и еще {len(users_list) - 10} пользователей"

                user_list_text += "\n\nУточните username"
                await message.answer(user_list_text)
                return

            # Если найден один пользователь
            user = users_list[0]
            stats = await session.get(UserStat, user.id)
            progress = await session.get(UserProgress, user.id)

            # Рассчитываем точность
            accuracy = 0
            if stats and stats.total_attempts > 0:
                accuracy = (stats.correct_answers / stats.total_attempts) * 100

            progress_text = (
                f"📊 Прогресс студента:\n"
                f"👤 ID: {user.id}\n"
                f"📛 Username: @{user.username or 'нет'}\n"
                f"🎯 Статус: {user.status.value}\n\n"
                f"📈 Статистика:\n"
                f"✅ Решено задач: {stats.total_attempts if stats else 0}\n"
                f"✔️ Правильных: {stats.correct_answers if stats else 0}\n"
                f"🎯 Точность: {accuracy:.1f}%\n\n"
                f"⚡ Прогресс:\n"
                f"💎 Всего XP: {progress.total_points if progress else 0}\n"
                f"📅 За неделю: {progress.weekly_points if progress else 0}\n"
                f"🔥 Серия дней: {progress.current_streak if progress else 0}\n"
                f"⏰ Последняя активность: {user.last_interaction_time.strftime('%d.%m.%Y %H:%M') if user.last_interaction_time else 'нет данных'}"
            )

            await message.answer(progress_text)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("send_feedback"), IsTeacherFilter())
async def cmd_send_feedback(message: types.Message, bot: Bot):
    """Отправить обратную связь студенту по username"""
    try:
        # Извлекаем username и сообщение из команды
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("❌ Использование: /send_feedback @username <сообщение>")
            return

        # Убираем @ и приводим к нижнему регистру
        username_search = parts[1].lstrip('@').lower()
        feedback_text = parts[2]

        async with AsyncSessionLocal() as session:
            # Ищем пользователя по части username
            users = await session.scalars(
                select(User).where(User.username.ilike(f"%{username_search}%"))
            )

            users_list = list(users)

            if not users_list:
                await message.answer("❌ Пользователь с таким username не найден")
                return

            if len(users_list) > 1:
                # Если найдено несколько пользователей
                user_list_text = "Найдено несколько пользователей:\n"
                for i, user in enumerate(users_list[:10], 1):
                    user_list_text += f"{i}. @{user.username} (ID: {user.id})\n"

                if len(users_list) > 10:
                    user_list_text += f"\n... и еще {len(users_list) - 10} пользователей"

                user_list_text += "\n\nУточните username"
                await message.answer(user_list_text)
                return

            # Если найден один пользователь
            user = users_list[0]

            # Пытаемся отправить сообщение
            try:
                await bot.send_message(
                    user.id,
                    f"📩 Обратная связь:\n\n{feedback_text}\n\n"
                    f"💡 Если у вас есть вопросы, обратитесь в поддержку."
                )
                await message.answer(f"✅ Сообщение отправлено пользователю @{user.username}")
            except Exception as e:
                await message.answer(f"❌ Не удалось отправить сообщение пользователю @{user.username}: {str(e)}")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("thelp"), IsTeacherFilter())
async def cmd_thelp(message: types.Message):
    """Помощь по командам преподавателя"""
    help_text = (
        "👨‍🏫 Команды преподавателя:\n\n"
        "/student_progress [@username] - Прогресс студента\n\n"
        "/send_feedback [@username] [message] - Отправить обратную связь"
    )
    await message.answer(help_text)
