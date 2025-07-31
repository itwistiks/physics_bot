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
    *,
    session: AsyncSession,
    message: Message | None = None,
    callback: CallbackQuery | None = None,
    task_id: int,
    user_answer: str,
    state: FSMContext
) -> bool:
    """Проверка ответа с полным обновлением статистики"""
    try:
        user_id = callback.from_user.id if callback else message.from_user.id

        # Обновляем weekly_points при необходимости
        from .stats_service import update_weekly_xp
        await update_weekly_xp(session, user_id)

        # Обновляем основную статистику
        from .stats_service import update_user_stats
        is_correct = str(user_answer).strip().lower() == str(
            (await session.get(Task, task_id)).correct_answer).strip().lower()

        if not await update_user_stats(session, user_id, task_id, is_correct):
            raise Exception("Failed to update user stats")

        # Отправляем результат пользователю
        result_text = f"{'✅ Правильно!' if is_correct else '❌ Неверно!'}"
        if callback:
            await callback.answer(result_text)
            await callback.message.answer(
                result_text,
                reply_markup=theory_solution_kb(task_id, (await session.get(Task, task_id)).complexity.value)
            )
        elif message:
            await message.answer(
                result_text,
                reply_markup=theory_solution_kb(task_id, (await session.get(Task, task_id)).complexity.value)
            )

        await state.set_state(TaskStates.SHOWING_RESULT)
        return True

    except Exception as e:
        logger.error(f"Error in check_answer: {e}", exc_info=True)
        error_msg = "⚠️ Ошибка при обновлении статистики"
        if callback:
            await callback.answer(error_msg, show_alert=True)
        elif message:
            await message.answer(error_msg)
        return False


async def stop_practice_session(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Практика завершена",
        reply_markup=practice_menu_kb()
    ), CallbackQuery
