from .task_utils import get_random_task  # Если нужно внутри этого файла
from core.database.models import Task, Theory
from core.fsm.states import TaskStates
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from ..keyboards.reply import (
    practice_menu_kb,
    task_navigation_kb
)
from ..keyboards.inline import (
    answer_options_kb,
    theory_solution_kb
)
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import random
from config.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


async def check_answer(
    session: AsyncSession,
    task_id: int,
    user_answer: str,
    user_id: int,
    state: FSMContext | None = None
) -> dict:  # ИЗМЕНИТЕ ТИП ВОЗВРАТА НА dict
    """Проверка ответа с полным обновлением статистики"""
    try:
        # Получаем задачу
        task = await session.get(Task, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"success": False, "error": "Task not found"}

        # Проверяем ответ
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
            logger.error(f"Failed to update stats for user {user_id}")
            return {"success": False, "error": "Failed to update stats"}

        # Если передан state, обновляем его
        if state:
            await state.set_state(TaskStates.SHOWING_RESULT)

        return {
            "success": True,
            "is_correct": is_correct,
            "task": task,
            "task_id": task_id,
            "complexity": task.complexity.value
        }

    except Exception as e:
        logger.error(f"Error in check_answer: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def stop_practice_session(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Практика завершена",
        reply_markup=practice_menu_kb()
    ), CallbackQuery
