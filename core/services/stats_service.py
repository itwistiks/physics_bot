from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, inspect
from core.database.models import UserStat, UserProgress, Task
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import selectinload
import logging

logger = logging.getLogger(__name__)


async def update_user_stats(
    session: AsyncSession,
    user_id: int,
    task_id: int,
    is_correct: bool
):
    """Обновление статистики с гарантированным коммитом"""
    try:
        task = await session.get(Task, task_id)
        if not task:
            return False

        # Получаем или создаем статистику
        user_stat = await session.get(UserStat, user_id)
        if not user_stat:
            user_stat = UserStat(user_id=user_id)
            session.add(user_stat)

        # Обновляем статистику
        user_stat.total_attempts += 1
        if is_correct:
            user_stat.correct_answers += 1
        user_stat.percentage = (
            user_stat.correct_answers / user_stat.total_attempts) * 100

        # Обновляем подтему (если есть)
        if task.subtopic_id:
            subtopic_key = str(task.subtopic_id)
            if subtopic_key not in user_stat.subtopics_stats:
                user_stat.subtopics_stats[subtopic_key] = {
                    "correct": 0, "wrong": 0}

            if is_correct:
                user_stat.subtopics_stats[subtopic_key]["correct"] += 1
            else:
                user_stat.subtopics_stats[subtopic_key]["wrong"] += 1

            flag_modified(user_stat, "subtopics_stats")

        # Явный flush, но не коммит (коммит будет в основном обработчике)
        await session.flush()
        return True

    except Exception as e:
        logger.error(f"Ошибка обновления статистики: {str(e)}")
        await session.rollback()
        return False

        # Обновляем прогресс
        points = 2 if is_correct else 1
        user_progress.total_points = (user_progress.total_points or 0) + points
        user_progress.weekly_points = (
            user_progress.weekly_points or 0) + points
        user_progress.daily_record = (user_progress.daily_record or 0) + 1

        # Обновляем статистику по подтеме
        task = await session.get(Task, task_id)
        if task and task.subtopic_id:
            subtopic_key = str(task.subtopic_id)
            if not user_stat.subtopics_stats:
                user_stat.subtopics_stats = {}
            if subtopic_key not in user_stat.subtopics_stats:
                user_stat.subtopics_stats[subtopic_key] = {
                    "correct": 0, "wrong": 0}

            if is_correct:
                user_stat.subtopics_stats[subtopic_key]["correct"] += 1
            else:
                user_stat.subtopics_stats[subtopic_key]["wrong"] += 1

            flag_modified(user_stat, "subtopics_stats")

        await session.commit()
        return True

    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating stats: {e}")
        raise


def calculate_percentage(user_stat: UserStat) -> float:
    """Вычисляем процент правильных ответов"""
    if user_stat.total_attempts == 0:
        return 0.0
    return (user_stat.correct_answers / user_stat.total_attempts) * 100


def update_subtopic_stats(user_stat: UserStat, subtopic_id: int, is_correct: bool):
    """Обновляем статистику по подтеме"""
    subtopic_key = str(subtopic_id)
    if subtopic_key not in user_stat.subtopics_stats:
        user_stat.subtopics_stats[subtopic_key] = {"correct": 0, "wrong": 0}

    if is_correct:
        user_stat.subtopics_stats[subtopic_key]["correct"] += 1
    else:
        user_stat.subtopics_stats[subtopic_key]["wrong"] += 1

    flag_modified(user_stat, "subtopics_stats")


def update_progress(user_progress: UserProgress, is_correct: bool):
    """Обновляем прогресс пользователя"""
    points = 2 if is_correct else 1
    user_progress.total_points += points
    user_progress.weekly_points += points
    user_progress.daily_record += 1


async def get_user_stats_summary(session: AsyncSession, user_id: int):
    """
    Возвращает сводную статистику пользователя
    """
    try:
        inspector = inspect(session.get_bind())
        if not all(inspector.has_table(table) for table in ['user_stats', 'user_progress']):
            return None

        user_stat = await session.get(UserStat, user_id)
        user_progress = await session.get(UserProgress, user_id)

        if not user_stat or not user_progress:
            return None

        return {
            "total_attempts": user_stat.total_attempts,
            "correct_answers": user_stat.correct_answers,
            "percentage": user_stat.percentage,
            "current_streak": user_progress.current_streak,
            "total_points": user_progress.total_points,
            "daily_record": user_progress.daily_record
        }

    except Exception as e:
        logger.error(f"Error getting user stats summary: {str(e)}")
        return None
