import random
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from config.database import AsyncSessionLocal
from core.database.models import Task
import logging

logger = logging.getLogger(__name__)


async def get_random_task(task_type: int = None) -> Task:
    async with AsyncSessionLocal() as session:
        stmt = select(Task)
        if task_type is not None:
            stmt = stmt.where(Task.type_number == task_type)
        stmt = stmt.options(selectinload(Task.topic))
        tasks = (await session.execute(stmt)).scalars().all()
        return random.choice(tasks) if tasks else None


async def get_shuffled_task_ids(task_type: int = None, limit: int = 20) -> list[int]:
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Task.id)
            if task_type is not None:
                stmt = stmt.where(Task.type_number == task_type)

            result = await session.execute(stmt)
            task_ids = [row[0] for row in result.all()]
            await session.commit()  # Явный коммит

            random.shuffle(task_ids)
            return task_ids[:limit]
        except Exception as e:
            await session.rollback()
            logger.error(f"Error getting task ids: {str(e)}")
            return []  # Возвращаем только лимитированное количество
