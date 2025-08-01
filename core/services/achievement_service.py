import logging
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.models import (
    UserAchievement,
    Achievement,
    User,
    UserStat,
    UserProgress,
    Task,
    Subtopic
)
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


async def check_and_unlock_achievements(
    session: AsyncSession,
    user_id: int,
    is_correct: bool,  # Добавляем параметр is_correct
    task_id: Optional[int] = None
) -> list[Achievement]:
    """Проверяет и разблокирует достижения пользователя."""
    try:
        # Получаем все достижения для проверки (без фильтра по типу)
        stmt = select(Achievement)
        achievements = (await session.execute(stmt)).scalars().all()

        unlocked = []
        for achievement in achievements:
            # Проверяем, не разблокировано ли уже достижение
            stmt_exists = select(UserAchievement).where(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement.id
                )
            )
            exists = (await session.execute(stmt_exists)).scalar_one_or_none()

            if not exists and await is_achievement_unlocked(
                session=session,
                user_id=user_id,
                achievement=achievement,
                is_correct=is_correct,  # Передаем is_correct
                task_id=task_id
            ):
                # Разблокируем достижение
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    unlocked_at=datetime.utcnow(),
                    progress=100
                )
                session.add(user_achievement)
                unlocked.append(achievement)
                logger.info(
                    f"User {user_id} unlocked achievement {achievement.name}")

        return unlocked

    except Exception as e:
        logger.error(
            f"Error in check_and_unlock_achievements: {e}", exc_info=True)
        return []


async def is_achievement_already_unlocked(
    session: AsyncSession,
    user_id: int,
    achievement_id: int
) -> bool:
    """Проверяет, есть ли у пользователя уже это достижение"""
    stmt = select(UserAchievement).where(
        and_(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def unlock_achievement(
    session: AsyncSession,
    user_id: int,
    achievement_id: int
) -> None:
    """Разблокирует достижение для пользователя"""
    user_achievement = UserAchievement(
        user_id=user_id,
        achievement_id=achievement_id,
        unlocked_at=datetime.utcnow(),
        progress=100
    )
    session.add(user_achievement)
    await session.flush()


async def is_achievement_unlocked(
    session: AsyncSession,
    user_id: int,
    achievement: Achievement,
    is_correct: bool,
    task_id: Optional[int] = None
) -> bool:
    """
    Проверяет условие конкретного достижения.
    Возвращает True, если условие выполнено.
    """
    try:
        condition = achievement.conditions.lower()

        # Разбираем условие по типам
        if "solved_tasks" in condition:
            return await check_solved_tasks_condition(session, user_id, condition)
        elif "correct_percentage" in condition:
            return await check_correct_percentage_condition(session, user_id, condition)
        elif "daily_streak" in condition:
            return await check_daily_streak_condition(session, user_id, condition)
        elif "topic_id" in condition and task_id:
            return await check_topic_condition(session, user_id, condition, task_id)
        elif "subtopic_id" in condition and task_id:
            return await check_subtopic_condition(session, user_id, condition, task_id)

        return False

    except Exception as e:
        logger.error(
            f"Error checking achievement condition: {e}", exc_info=True)
        return False


async def check_solved_tasks_condition(
    session: AsyncSession,
    user_id: int,
    condition: str
) -> bool:
    """Проверяет условие на количество решенных задач"""
    try:
        # Пример условия: "solved_tasks >= 10"
        parts = condition.split()
        if len(parts) < 3 or parts[0] != "solved_tasks":
            return False

        operator = parts[1]
        required = int(parts[2])

        # Получаем статистику пользователя
        user_stat = await session.get(UserStat, user_id)
        if not user_stat:
            return False

        solved = user_stat.correct_answers

        # Применяем оператор сравнения
        if operator == ">=":
            return solved >= required
        elif operator == ">":
            return solved > required
        elif operator == "<=":
            return solved <= required
        elif operator == "<":
            return solved < required
        elif operator == "==":
            return solved == required

        return False

    except Exception as e:
        logger.error(f"Error in check_solved_tasks_condition: {e}")
        return False


async def check_correct_percentage_condition(
    session: AsyncSession,
    user_id: int,
    condition: str
) -> bool:
    """Проверяет условие на процент правильных ответов"""
    try:
        # Пример условия: "correct_percentage > 80 AND topic_id = 3"
        parts = condition.split()
        if len(parts) < 3 or parts[0] != "correct_percentage":
            return False

        operator = parts[1]
        required = float(parts[2])

        # Получаем статистику пользователя
        user_stat = await session.get(UserStat, user_id)
        if not user_stat:
            return False

        percentage = user_stat.percentage

        # Применяем оператор сравнения
        if operator == ">=":
            return percentage >= required
        elif operator == ">":
            return percentage > required
        elif operator == "<=":
            return percentage <= required
        elif operator == "<":
            return percentage < required
        elif operator == "==":
            return percentage == required

        return False

    except Exception as e:
        logger.error(f"Error in check_correct_percentage_condition: {e}")
        return False


async def check_daily_streak_condition(
    session: AsyncSession,
    user_id: int,
    condition: str
) -> bool:
    """Проверяет условие на серию дней активности"""
    try:
        # Пример условия: "daily_streak >= 5"
        parts = condition.split()
        if len(parts) < 3 or parts[0] != "daily_streak":
            return False

        operator = parts[1]
        required = int(parts[2])

        # Получаем прогресс пользователя
        user_progress = await session.get(UserProgress, user_id)
        if not user_progress:
            return False

        streak = user_progress.current_streak

        # Применяем оператор сравнения
        if operator == ">=":
            return streak >= required
        elif operator == ">":
            return streak > required
        elif operator == "<=":
            return streak <= required
        elif operator == "<":
            return streak < required
        elif operator == "==":
            return streak == required

        return False

    except Exception as e:
        logger.error(f"Error in check_daily_streak_condition: {e}")
        return False


async def check_topic_condition(
    session: AsyncSession,
    user_id: int,
    condition: str,
    task_id: int
) -> bool:
    """Проверяет условие, связанное с конкретной темой"""
    try:
        # Пример условия: "solved_tasks >= 10 AND topic_id = 3"
        task = await session.get(Task, task_id)
        if not task:
            return False

        # Проверяем, что условие содержит нужную тему
        topic_part = next((p for p in condition.split()
                          if p.startswith("topic_id")), None)
        if not topic_part:
            return False

        # Получаем ID темы из условия
        topic_id = int(topic_part.split("=")[1])

        # Проверяем, что задача относится к нужной теме
        return task.topic_id == topic_id

    except Exception as e:
        logger.error(f"Error in check_topic_condition: {e}")
        return False


async def check_subtopic_condition(
    session: AsyncSession,
    user_id: int,
    condition: str,
    task_id: int
) -> bool:
    """Проверяет условие, связанное с конкретной подтемой"""
    try:
        # Пример условия: "solved_tasks >= 5 AND subtopic_id = 12"
        task = await session.get(Task, task_id)
        if not task or not task.subtopic_id:
            return False

        # Проверяем, что условие содержит нужную подтему
        subtopic_part = next((p for p in condition.split()
                              if p.startswith("subtopic_id")), None)
        if not subtopic_part:
            return False

        # Получаем ID подтемы из условия
        subtopic_id = int(subtopic_part.split("=")[1])

        # Проверяем, что задача относится к нужной подтеме
        return task.subtopic_id == subtopic_id

    except Exception as e:
        logger.error(f"Error in check_subtopic_condition: {e}")
        return False


async def get_user_achievements(
    session: AsyncSession,
    user_id: int
) -> list[tuple[UserAchievement, Achievement]]:
    """
    Возвращает список достижений пользователя с информацией о каждом достижении.
    """
    try:
        stmt = (
            select(UserAchievement, Achievement)
            .join(Achievement, UserAchievement.achievement_id == Achievement.id)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.unlocked_at.desc())
        )
        result = await session.execute(stmt)
        return result.all()
    except Exception as e:
        logger.error(f"Error in get_user_achievements: {e}", exc_info=True)
        return []
