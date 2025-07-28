import logging
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from core.database.models import User, UserStat, UserProgress, Topic, Subtopic

logger = logging.getLogger(__name__)


async def get_or_create_user(session: AsyncSession, user_id: int, username: str = None) -> User:
    """
    Получает или создает пользователя с начальной статистикой и прогрессом
    """
    try:
        # 1. Получаем или создаем пользователя
        user = await session.get(User, user_id)

        if user is None:
            logger.info(f"Creating new user {user_id}")
            user = User(
                id=user_id,
                username=username,
                registration_date=datetime.utcnow(),
                status='no_sub',
                last_interaction_time=datetime.utcnow()
            )
            session.add(user)
            await session.commit()
            logger.info(f"User {user_id} created successfully")

            # 2. Создаем запись прогресса
            progress = UserProgress(user_id=user_id)
            session.add(progress)

            # 3. Создаем начальную статистику
            stat = UserStat(
                user_id=user_id,
                subtopics_stats={},
                correct_answers=0,
                total_attempts=0,
                percentage=0.0
            )
            session.add(stat)

            await session.commit()
            logger.info(
                f"Initial stats and progress created for user {user_id}")

            # 4. Инициализируем статистику по подтемам (опционально)
            await initialize_subtopic_stats(session, user_id)
        else:
            logger.info(f"Updating existing user {user_id}")
            user.last_interaction_time = datetime.utcnow()
            if username and user.username != username:
                user.username = username
            await session.commit()

        return user

    except SQLAlchemyError as e:
        logger.error(
            f"Database error in get_or_create_user: {str(e)}", exc_info=True)
        await session.rollback()
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in get_or_create_user: {str(e)}", exc_info=True)
        await session.rollback()
        raise


async def initialize_subtopic_stats(session: AsyncSession, user_id: int):
    """
    Инициализирует статистику по всем подтемам для нового пользователя
    """
    try:
        subtopics = await session.execute(select(Subtopic))
        subtopics = subtopics.scalars().all()

        if not subtopics:
            logger.warning("No subtopics found in database!")
            return

        user_stat = await session.get(UserStat, user_id)
        if not user_stat:
            logger.error(f"UserStat not found for user {user_id}")
            return

        # Инициализируем нулевые значения для всех подтем
        for subtopic in subtopics:
            if str(subtopic.id) not in user_stat.subtopics_stats:
                user_stat.subtopics_stats[str(subtopic.id)] = {
                    "correct": 0,
                    "wrong": 0
                }

        logger.debug(f"Before flag_modified: {user_stat.subtopics_stats}")
        flag_modified(user_stat, "subtopics_stats")
        logger.debug(f"After flag_modified: {user_stat.subtopics_stats}")

        # Помечаем поле как измененное
        flag_modified(user_stat, "subtopics_stats")

        await session.commit()
        logger.info(f"Initialized subtopic stats for user {user_id}")

    except SQLAlchemyError as e:
        logger.error(
            f"Database error in initialize_subtopic_stats: {str(e)}", exc_info=True)
        await session.rollback()
        raise


async def update_user_stats(
    session: AsyncSession,
    user_id: int,
    subtopic_id: int,
    is_correct: bool
):
    """
    Обновляет статистику пользователя после ответа на задание
    """
    try:
        user_stat = await session.get(UserStat, user_id)
        if not user_stat:
            logger.error(f"UserStat not found for user {user_id}")
            return

        # Обновляем общую статистику
        user_stat.total_attempts += 1
        if is_correct:
            user_stat.correct_answers += 1
        user_stat.percentage = (user_stat.correct_answers / user_stat.total_attempts) * \
            100 if user_stat.total_attempts > 0 else 0

        # Обновляем статистику по подтеме
        subtopic_key = str(subtopic_id)
        if subtopic_key not in user_stat.subtopics_stats:
            user_stat.subtopics_stats[subtopic_key] = {
                "correct": 0, "wrong": 0}

        if is_correct:
            user_stat.subtopics_stats[subtopic_key]["correct"] += 1
        else:
            user_stat.subtopics_stats[subtopic_key]["wrong"] += 1

        await session.commit()
        logger.debug(
            f"Updated stats for user {user_id}, subtopic {subtopic_id}, correct: {is_correct}")

    except SQLAlchemyError as e:
        logger.error(
            f"Database error in update_user_stats: {str(e)}", exc_info=True)
        await session.rollback()
        raise


async def log_user_stats(session: AsyncSession, user_id: int):
    """
    Логирует текущую статистику пользователя (для отладки)
    """
    try:
        user_stat = await session.get(UserStat, user_id)
        if not user_stat:
            logger.warning(f"No stats found for user {user_id}")
            return 0

        logger.debug(f"Stats for user {user_id}:")
        logger.debug(
            f"Total: correct={user_stat.correct_answers}, attempts={user_stat.total_attempts}, percentage={user_stat.percentage:.1f}%")

        for subtopic_id, stats in user_stat.subtopics_stats.items():
            logger.debug(
                f"Subtopic {subtopic_id}: correct={stats['correct']}, wrong={stats['wrong']}")

        return len(user_stat.subtopics_stats)

    except SQLAlchemyError as e:
        logger.error(f"Error logging stats for user {user_id}: {str(e)}")
        return 0
