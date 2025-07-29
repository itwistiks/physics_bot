from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import random
from config.database import AsyncSessionLocal

from ..keyboards.inline import (
    answer_options_kb,
    theory_solution_kb
)
from ..keyboards.reply import (
    practice_menu_kb,
    task_navigation_kb
)

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup

from core.fsm.states import TaskStates
from core.database.models import Task, Theory
from .task_utils import get_random_task  # Если нужно внутри этого файла


async def check_answer(callback: CallbackQuery, task_id: int, answer_idx: int) -> bool:
    async with AsyncSessionLocal() as session:
        task = await session.get(Task, task_id)
        if not task:
            await callback.answer("Задание не найдено", show_alert=True)
            return False

        is_correct = (task.answer_options[answer_idx] == task.correct_answer)
        await callback.answer(
            "✅ Правильно!" if is_correct else "❌ Неверно!",
            show_alert=True
        )

        return is_correct


async def stop_practice_session(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Практика завершена",
        reply_markup=practice_menu_kb()
    ), CallbackQuery
