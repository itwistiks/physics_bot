from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy import select
from sqlalchemy.orm import selectinload
import random

from config.database import AsyncSessionLocal
from core.database.models import Task, Theory
from core.services.task_display import display_task

from ..keyboards.inline import (
    part_one_types_kb,
    answer_options_kb,
    theory_solution_kb
)
from ..keyboards.reply import (
    practice_menu_kb,
    task_navigation_kb
)

from core.services.task_display import display_task, display_task_by_id
from core.services.task_utils import get_shuffled_task_ids
# from core.services.answer_processing import process_answer
from core.services.answer_checker import check_answer

import logging


logger = logging.getLogger(__name__)


router = Router()

# Состояния для FSM


class TaskStates(StatesGroup):
    WAITING_ANSWER = State()
    SHOWING_RESULT = State()


@router.callback_query(F.data.startswith("part_one:"))
async def handle_task_type(callback: CallbackQuery, state: FSMContext):
    task_type = int(callback.data.split(":")[1])

    # Получаем перемешанные ID заданий КОНКРЕТНОГО типа
    task_ids = await get_shuffled_task_ids(task_type=task_type)

    if not task_ids:
        await callback.answer("Задания этого типа не найдены", show_alert=True)
        return

    await state.update_data(
        TASK_LIST=task_ids,
        CURRENT_INDEX=0,
        IS_RANDOM_SESSION=False  # Флаг, что это сессия по типу
    )

    await display_task_by_id(callback.message, task_ids[0], state)
    await callback.answer()


async def show_random_task(message: Message, task_type: int, state: FSMContext):
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Task).where(
                Task.type_number == task_type
            ).options(selectinload(Task.topic))

            tasks = (await session.execute(stmt)).scalars().all()

            if not tasks:
                await message.answer("Задания этого типа не найдены")
                return

            task = random.choice(tasks)
            await state.update_data(current_task_id=task.id)
            await display_task(message, task, state)
    except Exception as e:
        await message.answer(f"Ошибка при загрузке задания: {e}")
        print(f"Ошибка: {e}")


@router.callback_query(F.data.startswith("answer:"))
async def handle_button_answer(callback: CallbackQuery):
    try:
        _, task_id, answer_idx = callback.data.split(":")
        task = None

        # Основная логика в отдельной функции
        async with AsyncSessionLocal() as session:
            task = await session.get(Task, int(task_id))

        if not task:
            await callback.answer("Задание не найдено", show_alert=True)
            return

        await check_answer(
            message=callback.message,
            task_id=task.id,
            user_answer=task.answer_options[int(answer_idx)],
            callback=callback
        )

    except Exception as e:
        logger.error(f"Button handler error: {e}")
        await callback.answer("Ошибка обработки", show_alert=True)


# -------------| Обработчики inline-кнопок после задачи |------------- #


# Обработчик теории


@router.callback_query(F.data.startswith("theory:"))
async def show_theory(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        # Загружаем задание вместе с теорией за один запрос
        stmt = select(Task).where(Task.id == task_id).options(
            selectinload(Task.theory))
        task = (await session.execute(stmt)).scalar_one_or_none()

        if not task:
            await callback.message.answer("⚠️ Задание не найдено")
            await callback.answer()
            return

        if task.theory:
            await callback.message.answer(
                f"📚 Теория по заданию {task.type_number}:\n\n{task.theory.content}",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                f"⚠️ Для задания {task.type_number} теория не найдена\n"
                f"ID задания: {task.id}, Theory ID: {task.theory_id}"
            )

    await callback.answer()


# Обработчик разбора


@router.callback_query(F.data.startswith("solution:"))
async def handle_solution(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    # Здесь должна быть логика показа разбора
    await callback.answer("Разбор будет здесь позже")
