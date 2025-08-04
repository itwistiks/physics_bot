from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, inspect
from core.database.models import (
    UserStat,
    UserProgress,
    Task,
    WeeklyXP,  # Не работает
    Subtopic,
    User,
    UserAchievement,
    Achievement,
    Complexity,
    UserStatus
)
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
    """Обновляет статистику с учетом всех требований"""
    try:
        # Получаем необходимые данные
        task = await session.get(Task, task_id)
        user = await session.get(User, user_id)

        if not task or not user:
            logger.error("Task or user not found")
            return False

        # Определяем количество очков
        if task.complexity == Complexity.BASIC:
            points = 2 if (is_correct and user.status == UserStatus.SUB) else \
                1 if (is_correct and user.status == UserStatus.NO_SUB) else \
                -1
        elif task.complexity == Complexity.ADVANCED:
            points = 6 if (is_correct and user.status == UserStatus.SUB) else \
                4 if (is_correct and user.status == UserStatus.NO_SUB) else \
                -2
        elif task.complexity == Complexity.HIGH:
            points = 20 if (is_correct and user.status == UserStatus.SUB) else \
                15 if (is_correct and user.status == UserStatus.NO_SUB) else \
                -6
        else:
            points = 0

        # Получаем или создаем записи статистики
        user_stat = await session.get(UserStat, user_id, with_for_update=True) or \
            UserStat(user_id=user_id)

        user_progress = await session.get(UserProgress, user_id, with_for_update=True) or \
            UserProgress(user_id=user_id)

        # Обновляем статистику
        user_stat.total_attempts += 1
        if is_correct:
            user_stat.correct_answers += 1
        user_stat.percentage = (
            user_stat.correct_answers / user_stat.total_attempts) * 100

        # Обновляем прогресс (защита от отрицательных значений)
        new_total = max(0, user_progress.total_points + points)
        new_weekly = max(0, user_progress.weekly_points + points)

        # Вычисляем current_streak
        today = datetime.utcnow().date()
        last_active = user_progress.last_active_day

        if last_active == today - timedelta(days=1):
            # Пользователь активен второй день подряд
            current_streak = user_progress.current_streak + 1
        elif last_active == today:
            # Уже активен сегодня - не увеличиваем streak
            current_streak = user_progress.current_streak
        else:
            # Перерыв - сбрасываем streak
            current_streak = 1

        # Применяем обновления
        user_progress.total_points = new_total
        user_progress.weekly_points = new_weekly
        user_progress.current_streak = current_streak
        user_progress.last_active_day = today
        user_progress.daily_record += 1

        # Обновляем статистику по подтеме
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

        # Гарантируем сохранение объектов
        session.add_all([user_stat, user_progress])
        await session.flush()

        logger.info(
            f"Updated stats for user {user_id}: "
            f"status={user.status.value}, "
            f"complexity={task.complexity.value}, "
            f"correct={is_correct}, "
            f"points={points}, "
            f"total={user_progress.total_points}, "
            f"weekly={user_progress.weekly_points}, "
            f"streak={current_streak} days"
        )

        return True

    except Exception as e:
        logger.error(f"Error updating stats: {e}", exc_info=True)
        await session.rollback()
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


async def calculate_user_level(total_xp: int) -> tuple[int, str]:
    """Вычисляет уровень и титул пользователя на основе XP"""
    levels = {
        0: "<b>Новичок</b> → Ученик (6 ур.)",
        500: "<b>Ученик</b> → Знаток (21 ур.)",
        2000: "<b>Знаток</b> → Эксперт (51 ур.)",
        5000: "<b>Эксперт</b> → Мастер (81 ур.)",
        8000: "<b>Мастер</b> → Гуру (131 ур.)",
        13000: "<b>Гуру</b> → Идеал (201 ур.)",
        20000: "<b>Идеал</b> → Всевышний (501 ур.)",
        50000: "<b>Всевышний</b> → Непостижимый (1001 ур.)",
        100000: "<b>Непостижимый</b>"
    }

    level = total_xp // 100 + 1
    title = next(
        (title for xp, title in sorted(levels.items(), reverse=True) if total_xp >= xp)
    )

    return level, title


async def get_user_stats(session: AsyncSession, user_id: int) -> dict:
    """Получает полную статистику пользователя"""
    try:
        async with session.begin():
            # Получаем основную статистику
            user_stat = await session.get(UserStat, user_id)
            user_progress = await session.get(UserProgress, user_id)

            if not user_stat or not user_progress:
                logger.warning(
                    f"User stats or progress not found for user {user_id}")
                return None

            # Получаем XP за неделю
            week_start = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
            weekly_xp = await session.scalar(
                select(func.sum(WeeklyXP.xp_earned))
                .where(and_(
                    WeeklyXP.user_id == user_id,
                    WeeklyXP.week_start_date == week_start
                ))
            ) or 0

            # Вычисляем уровень и титул
            level, title = await calculate_user_level(user_progress.total_points)

            # Находим лучшую и худшую тему
            best_topic = worst_topic = None
            best_topic_accuracy = worst_topic_accuracy = 0

            if user_stat.subtopics_stats:
                try:
                    sorted_topics = sorted(
                        [(k, v) for k, v in user_stat.subtopics_stats.items()
                         if isinstance(v, dict)],
                        key=lambda x: (x[1].get('correct', 0) / (x[1].get('correct', 0) + x[1].get('wrong', 1))
                                       if (x[1].get('correct', 0) + x[1].get('wrong', 0)) > 0 else 0),
                        reverse=True
                    )

                    if sorted_topics:
                        best_id, best_stats = sorted_topics[0]
                        worst_id, worst_stats = sorted_topics[-1]

                        best_topic = await session.get(Subtopic, int(best_id))
                        worst_topic = await session.get(Subtopic, int(worst_id))

                        best_total = best_stats.get(
                            'correct', 0) + best_stats.get('wrong', 0)
                        best_topic_accuracy = (best_stats.get(
                            'correct', 0) / best_total) * 100 if best_total > 0 else 0

                        worst_total = worst_stats.get(
                            'correct', 0) + worst_stats.get('wrong', 0)
                        worst_topic_accuracy = (worst_stats.get(
                            'correct', 0) / worst_total) * 100 if worst_total > 0 else 0
                except Exception as e:
                    logger.error(f"Error processing subtopics stats: {e}")

            # Получаем рейтинги
            global_rank = await get_global_rank(session, user_id) or 0
            weekly_rank = await get_weekly_rank(session, user_id) or 0

            # Получаем информацию о достижениях
            achievements_unlocked = await session.scalar(
                select(func.count(UserAchievement.achievement_id))
                .where(and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.unlocked_at.is_not(None)
                ))
            ) or 0

            achievements_total = await session.scalar(select(func.count(Achievement.id))) or 0

            stats_data = {
                "total_xp": user_progress.total_points or 0,
                "weekly_xp": user_progress.weekly_points,
                "level": (level or 0, title or "Новичок"),
                "streak": user_progress.current_streak or 0,
                "total_tasks": user_stat.total_attempts or 0,
                "accuracy": user_stat.percentage or 0,
                "best_topic": best_topic,
                "best_topic_accuracy": best_topic_accuracy,
                "worst_topic": worst_topic,
                "worst_topic_accuracy": worst_topic_accuracy,
                "global_rank": global_rank,
                "weekly_rank": weekly_rank,
                "achievements_unlocked": achievements_unlocked,
                "achievements_total": achievements_total
            }

            logger.info(f"Successfully collected stats for user {user_id}")
            return stats_data

    except Exception as e:
        logger.error(f"Error in get_user_stats: {e}", exc_info=True)
        return None


async def get_global_rank(session: AsyncSession, user_id: int) -> int:
    """
    Получает глобальный рейтинг пользователя по общему количеству XP (total_points)
    Возвращает позицию в рейтинге (1-based) или 0 если пользователь не найден
    """
    try:
        # Создаем CTE для ранжирования пользователей
        rank_query = (
            select(
                UserProgress.user_id,
                UserProgress.total_points,
                func.rank().over(order_by=UserProgress.total_points.desc()).label('rank')
            )
            .select_from(UserProgress)
            .join(User, User.id == UserProgress.user_id)
            # Исключаем админов и модераторов
            .where(User.status.not_in(['admin', 'moderator']))
            .cte('user_ranks')
        )

        # Получаем ранг конкретного пользователя
        result = await session.execute(
            select(rank_query.c.rank)
            .where(rank_query.c.user_id == user_id)
        )

        return result.scalar() or 0

    except Exception as e:
        logger.error(f"Error getting global rank: {e}")
        return 0


async def get_weekly_rank(session: AsyncSession, user_id: int) -> int:
    """
    Получает недельный рейтинг пользователя по weekly_points
    Возвращает позицию в рейтинге (1-based) или 0 если пользователь не найден
    """
    try:
        # Создаем CTE для ранжирования пользователей по weekly_points
        rank_query = (
            select(
                UserProgress.user_id,
                UserProgress.weekly_points,
                func.rank().over(order_by=UserProgress.weekly_points.desc()).label('rank')
            )
            .select_from(UserProgress)
            .join(User, User.id == UserProgress.user_id)
            # Исключаем админов и модераторов
            .where(User.status.not_in(['admin', 'moderator']))
            .cte('weekly_ranks')
        )

        # Получаем ранг конкретного пользователя
        result = await session.execute(
            select(rank_query.c.rank)
            .where(rank_query.c.user_id == user_id)
        )

        return result.scalar() or 0

    except Exception as e:
        logger.error(f"Error getting weekly rank: {e}")
        return 0


async def update_weekly_xp(session: AsyncSession, user_id: int) -> bool:
    """Обновление weekly_points в начале новой недели"""
    try:
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())

        async with session.begin():
            user_progress = await session.get(UserProgress, user_id, with_for_update=True)
            if not user_progress:
                logger.error(f"UserProgress not found for {user_id}")
                return False

            # Если последняя активность была на прошлой неделе
            if user_progress.last_active_day and user_progress.last_active_day < week_start:
                # Сбрасываем weekly_points при переходе на новую неделю
                user_progress.weekly_points = 0
                logger.info(f"Reset weekly points for user {user_id}")
                await session.flush()

            return True

    except Exception as e:
        logger.error(f"Error updating weekly XP: {e}")
        await session.rollback()
        return False


async def reset_all_weekly_points(session: AsyncSession) -> int:
    """Обнуляет weekly_points у всех пользователей и возвращает количество обновленных записей"""
    try:
        result = await session.execute(
            update(UserProgress)
            .values(weekly_points=0)
        )
        await session.commit()
        return result.rowcount
    except Exception as e:
        logger.error(f"Error resetting weekly points: {e}")
        await session.rollback()
        return 0
