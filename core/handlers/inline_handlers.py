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
async def handle_button_answer(callback: CallbackQuery, state: FSMContext):
    try:
        # Проверяем текущее состояние пользователя
        current_state = await state.get_state()
        if current_state != TaskStates.WAITING_ANSWER.state:
            await callback.answer("Это задание уже проверено", show_alert=True)
            return

        # Разбираем данные callback
        _, task_id, answer_idx = callback.data.split(":")
        task_id = int(task_id)
        answer_idx = int(answer_idx)

        # Сразу отвечаем на callback, чтобы убрать анимацию
        await callback.answer()

        async with AsyncSessionLocal() as session:
            # Начинаем транзакцию
            async with session.begin():
                # Получаем задание с блокировкой FOR UPDATE
                task = await session.execute(
                    select(Task)
                    .where(Task.id == task_id)
                    .with_for_update()
                )
                task = task.scalar_one_or_none()

                if not task:
                    await callback.message.answer("Задание не найдено")
                    return

                # Проверяем ответ
                user_answer = task.answer_options[answer_idx]
                is_correct = str(user_answer).strip().lower() == str(
                    task.correct_answer).strip().lower()

                # Обновляем состояние
                await state.set_state(TaskStates.SHOWING_RESULT)

                # Обновляем статистику
                # await update_user_stats(
                #     session=session,
                #     user_id=callback.from_user.id,
                #     task_id=task.id,
                #     is_correct=is_correct
                # )

        # # Редактируем исходное сообщение с заданием
        # await callback.message.edit_reply_markup(
        #     reply_markup=None  # Убираем кнопки ответов
        # )

        # Отправляем результат
        result_message = await callback.message.answer(
            f"{'✅ Правильно!' if is_correct else '❌ Неверно!'}",
            reply_markup=theory_solution_kb(task.id, task.complexity.value)
        )

        # Сохраняем ID сообщения с результатом /
        # await state.update_data(result_message_id=result_message.message_id)

    except Exception as e:
        logger.error(f"Error in handle_button_answer: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при проверке ответа", show_alert=True)


# -------------| Обработчики inline-кнопок после задачи |------------- #


# Обработчик теории


@router.callback_query(F.data.startswith("theory:"))
async def show_theory(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():  # Явное управление транзакцией
                stmt = select(Task).where(Task.id == task_id).options(
                    selectinload(Task.theory).selectinload(Theory.topic)
                )
                task = (await session.execute(stmt)).scalar_one_or_none()

                if not task:
                    await callback.answer("⚠️ Задание не найдено", show_alert=True)
                    return  # Транзакция завершится автоматически

                if not task.theory:
                    await callback.answer("⚠️ Теория отсутствует", show_alert=True)
                    return

                topic_name = task.theory.topic.title_ru if task.theory.topic else "Без темы"
                theory_text = (
                    f"📚 Теория по заданию {task.type_number}\n"
                    f"Тема: {topic_name}\n\n"
                    f"{task.theory.content}"
                )

                try:
                    await callback.message.answer(theory_text, parse_mode="Markdown")
                except Exception as e:
                    logger.error(f"Markdown error: {e}")
                    await callback.message.answer(theory_text)

                # Транзакция закоммитится автоматически при выходе из блока

        except Exception as e:
            logger.error(f"Database error: {e}", exc_info=True)
            await callback.answer("⚠️ Ошибка загрузки теории", show_alert=True)
        finally:
            await callback.answer()  # Всегда отвечаем на callback


# Обработчик разбора


@router.callback_query(F.data.startswith("solution:"))
async def handle_solution(callback: CallbackQuery):
    try:
        task_id = int(callback.data.split(":")[1])

        async with AsyncSessionLocal() as session:
            # Явно начинаем транзакцию
            async with session.begin():
                # Получаем задачу с блокировкой для чтения
                task = await session.execute(
                    select(Task)
                    .where(Task.id == task_id)
                    .with_for_update(read=True)
                )
                task = task.scalar_one_or_none()

                if not task:
                    await callback.answer("⚠️ Задача не найдена", show_alert=True)
                    return

                if not task.video_analysis_url:
                    await callback.answer("⚠️ Видеоразбор отсутствует", show_alert=True)
                    return

                # Отправляем сообщение с видеоразбором
                await callback.message.answer(
                    f"🎥 Видеоразбор к задаче {task.type_number}:\n"
                    f"{task.video_analysis_url}"
                )

        # Убираем уведомление "загрузка" у кнопки
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в handle_solution: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка загрузки видеоразбора", show_alert=True)
