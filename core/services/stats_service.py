from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from core.database.models import UserStat


async def update_user_stats(
    session: AsyncSession,
    user_id: int,
    topic_id: int,
    subtopic_id: int = None,
    is_correct: bool = True
):
    # Находим или создаем запись статистики
    stat = await session.scalar(
        select(UserStat)
        .where(
            (UserStat.user_id == user_id) &
            (UserStat.topic_id == topic_id) &
            (UserStat.subtopic_id == subtopic_id)
        )
    )

    if not stat:
        stat = UserStat(
            user_id=user_id,
            topic_id=topic_id,
            subtopic_id=subtopic_id
        )
        session.add(stat)

    # Обновляем статистику
    stat.total_attempts += 1
    if is_correct:
        stat.correct_answers += 1

    # Пересчитываем процент
    if stat.total_attempts > 0:
        stat.percentage = (stat.correct_answers / stat.total_attempts) * 100

    await session.commit()
    return stat
