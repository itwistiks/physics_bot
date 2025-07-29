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
) -> bool:
    """Атомарное обновление статистики пользователя с блокировкой"""
    try:
        # Получаем задание для определения подтемы
        task = await session.get(Task, task_id)
        if not task:
            return False

        # Получаем статистику пользователя с блокировкой
        user_stat = await session.execute(
            select(UserStat)
            .where(UserStat.user_id == user_id)
            .with_for_update()
        )
        user_stat = user_stat.scalar_one_or_none()

        if not user_stat:
            user_stat = UserStat(user_id=user_id)
            session.add(user_stat)

        # Получаем прогресс пользователя с блокировкой
        user_progress = await session.execute(
            select(UserProgress)
            .where(UserProgress.user_id == user_id)
            .with_for_update()
        )
        user_progress = user_progress.scalar_one_or_none()

        if not user_progress:
            user_progress = UserProgress(user_id=user_id)
            session.add(user_progress)

        # Обновляем общую статистику
        user_stat.total_attempts += 1
        if is_correct:
            user_stat.correct_answers += 1
        user_stat.percentage = calculate_percentage(user_stat)

        # Обновляем статистику по подтеме (если есть)
        if task.subtopic_id:
            update_subtopic_stats(user_stat, task.subtopic_id, is_correct)

        # Обновляем прогресс
        update_progress(user_progress, is_correct)

        # Обновляем дату последней активности
        user_progress.last_active_day = datetime.utcnow().date()

        # Проверяем и обновляем серию дней
        if user_progress.last_active_day == datetime.utcnow().date() - timedelta(days=1):
            user_progress.current_streak += 1
        else:
            user_progress.current_streak = 1

        await session.commit()
        return True

    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating stats: {e}", exc_info=True)
        return False


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
