import random
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from config.database import AsyncSessionLocal
from core.database.models import Task, PartNumber
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


async def get_shuffled_task_ids(
        task_type: int = None,
        part_number: PartNumber = None,
        subtopic_id: int = None,
        limit: int = 20
) -> list[int]:
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Task.id)

            # Добавляем условия фильтрации, если они указаны
            filters = []
            if task_type is not None:
                filters.append(Task.type_number == task_type)
            if part_number is not None:
                filters.append(Task.part_number == part_number)
            if subtopic_id is not None:
                filters.append(Task.subtopic_id == subtopic_id)

            if filters:
                stmt = stmt.where(and_(*filters))

            result = await session.execute(stmt)
            task_ids = [row[0] for row in result.all()]

            random.shuffle(task_ids)
            return task_ids[:limit]

        except Exception as e:
            logger.error(f"Error getting task ids: {str(e)}")
            return []


async def get_variant_task_ids() -> list[int]:
    """Возвращает список ID заданий (по одному случайному каждого типа)"""
    async with AsyncSessionLocal() as session:
        try:
            # Получаем все существующие типы заданий
            stmt = select(Task.type_number).distinct().order_by(
                Task.type_number)
            type_numbers = (await session.execute(stmt)).scalars().all()

            task_ids = []

            # Для каждого типа получаем одно случайное задание
            for type_num in type_numbers:
                stmt = select(Task.id).where(
                    Task.type_number == type_num
                ).order_by(func.random()).limit(1)

                task_id = (await session.execute(stmt)).scalar_one_or_none()
                if task_id:
                    task_ids.append(task_id)

            return task_ids

        except Exception as e:
            logger.error(f"Error getting variant tasks: {str(e)}")
            return []
