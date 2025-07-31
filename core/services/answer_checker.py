from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from core.keyboards.inline import theory_solution_kb
from core.database.models import Task
from sqlalchemy import select
from core.fsm.states import TaskStates
import logging

logger = logging.getLogger(__name__)


async def check_answer(
    session: AsyncSession,
    task_id: int,
    user_answer: str,
    user_id: int
) -> dict:
    """Проверяет ответ без создания новой транзакции"""
    try:
        task = await session.get(Task, task_id, with_for_update=True)
        if not task:
            return {"error": "Task not found"}

        is_correct = str(user_answer).strip().lower() == str(
            task.correct_answer).strip().lower()

        # Обновляем статистику
        from .stats_service import update_user_stats
        update_success = await update_user_stats(
            session=session,
            user_id=user_id,
            task_id=task_id,
            is_correct=is_correct
        )

        if not update_success:
            return {"error": "Failed to update stats"}

        return {
            "is_correct": is_correct,
            "task_id": task_id,
            "complexity": task.complexity.value
        }

    except Exception as e:
        logger.error(f"Error in check_answer: {e}", exc_info=True)
        return {"error": str(e)}
