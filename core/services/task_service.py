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
from core.services.answer_checker import check_answer as check_answer_with_achievements

logger = logging.getLogger(__name__)


async def check_answer(
    session: AsyncSession,
    task_id: int,
    user_answer: str,
    user_id: int,
    state: FSMContext | None = None
) -> dict:
    """Проверка ответа с полным обновлением статистики"""
    try:
        return await check_answer_with_achievements(session, task_id, user_answer, user_id)

    except Exception as e:
        logger.error(f"Error in check_answer: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def stop_practice_session(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Практика завершена",
        reply_markup=practice_menu_kb()
    ), CallbackQuery
