from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import random

from config.database import AsyncSessionLocal
from core.database.models import Task, Theory, PartNumber, Complexity
from core.services.task_display import display_task

from ..keyboards.inline import (
    part_one_types_kb,
    answer_options_kb,
    theory_solution_kb,
    achievements_button
)
from ..keyboards.reply import (
    practice_menu_kb,
    task_navigation_kb
)

from core.services.task_display import display_task, display_task_by_id
from core.services.task_utils import get_shuffled_task_ids
# from core.services.answer_processing import process_answer
from core.services.answer_checker import check_answer

from core.utils.debounce import throttle

import logging


logger = logging.getLogger(__name__)


router = Router()

# Состояния для FSM


class TaskStates(StatesGroup):
    WAITING_ANSWER = State()
    SHOWING_RESULT = State()


@router.callback_query(F.data == "show_achievements")
async def show_achievements_handler(callback: CallbackQuery):
    """Обработчик кнопки просмотра достижений"""
    try:
        # Отвечаем всплывающим сообщением
        await callback.answer(
            "⏳ Система достижений пока в разработке",
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error in achievements handler: {e}")


@router.callback_query(F.data.startswith("part_one:"))
@throttle(2.0)
async def handle_task_type(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        # Удаляем сообщение с кнопками выбора типа
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id
            )
        except Exception as e:
            logger.warning(f"Could not delete message: {e}")

        task_type = int(callback.data.split(":")[1])

        async with AsyncSessionLocal() as session:
            stmt = select(Task.id).where(
                and_(
                    Task.type_number == task_type,
                    Task.part_number == PartNumber.PART_ONE
                )
            )
            result = await session.execute(stmt)
            task_ids = [row[0] for row in result.all()]

        if not task_ids:
            await callback.answer("Задания этого типа не найдены", show_alert=True)
            return

        random.shuffle(task_ids)

        await state.update_data(
            TASK_LIST=task_ids,
            CURRENT_INDEX=0,
            IS_RANDOM_SESSION=False,
            CURRENT_TASK_TYPE=task_type,
            CURRENT_PART=PartNumber.PART_ONE
        )

        await display_task_by_id(callback.message, task_ids[0], state)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in handle_part_two_task_type: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при загрузке заданий", show_alert=True)


@router.callback_query(F.data.startswith("part_two:"))
@throttle(2.0)
async def handle_part_two_task_type(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        # Удаляем сообщение с кнопками выбора типа
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id
            )
        except Exception as e:
            logger.warning(f"Could not delete message: {e}")

        task_type = int(callback.data.split(":")[1])

        async with AsyncSessionLocal() as session:
            stmt = select(Task.id).where(
                and_(
                    Task.type_number == task_type,
                    Task.part_number == PartNumber.PART_TWO
                )
            )
            result = await session.execute(stmt)
            task_ids = [row[0] for row in result.all()]

        if not task_ids:
            await callback.answer("Задания этого типа не найдены", show_alert=True)
            return

        random.shuffle(task_ids)

        await state.update_data(
            TASK_LIST=task_ids,
            CURRENT_INDEX=0,
            IS_RANDOM_SESSION=False,
            CURRENT_TASK_TYPE=task_type,
            CURRENT_PART=PartNumber.PART_TWO
        )

        await display_task_by_id(callback.message, task_ids[0], state)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in handle_part_two_task_type: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при загрузке заданий", show_alert=True)


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


@router.callback_query(F.data.startswith("subtopic:"))
@throttle(2.0)
async def handle_subtopic_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        # Удаляем сообщение с кнопками выбора типа
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id
            )
        except Exception as e:
            logger.warning(f"Could not delete message: {e}")

        subtopic_id = int(callback.data.split(":")[1])

        # Получаем все задания для выбранной подтемы
        async with AsyncSessionLocal() as session:
            stmt = select(Task.id).where(
                Task.subtopic_id == subtopic_id
            )
            result = await session.execute(stmt)
            task_ids = [row[0] for row in result.all()]

        if not task_ids:
            await callback.answer("Задания по этой теме не найдены", show_alert=True)
            return

        # Перемешиваем задания
        random.shuffle(task_ids)

        await state.update_data(
            TASK_LIST=task_ids,
            CURRENT_INDEX=0,
            IS_RANDOM_SESSION=False,
            CURRENT_SUBTOPIC_ID=subtopic_id
        )

        # Отображаем первое задание
        await display_task_by_id(callback.message, task_ids[0], state)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in handle_subtopic_selection: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при загрузке заданий", show_alert=True)


@router.callback_query(F.data.startswith("difficult_subtopic:"))
@throttle(2.0)
async def handle_difficult_subtopic_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        # Удаляем сообщение с кнопками выбора типа
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id
            )
        except Exception as e:
            logger.warning(f"Could not delete message: {e}")

        subtopic_id = int(callback.data.split(":")[1])

        # Получаем только сложные задания для выбранной подтемы
        async with AsyncSessionLocal() as session:
            stmt = select(Task.id).where(
                and_(
                    Task.subtopic_id == subtopic_id,
                    Task.complexity == Complexity.HIGH
                )
            )
            result = await session.execute(stmt)
            task_ids = [row[0] for row in result.all()]

        if not task_ids:
            await callback.answer("Сложные задания по этой теме не найдены", show_alert=True)
            return

        # Перемешиваем задания
        random.shuffle(task_ids)

        await state.update_data(
            TASK_LIST=task_ids,
            CURRENT_INDEX=0,
            IS_RANDOM_SESSION=False,
            CURRENT_SUBTOPIC_ID=subtopic_id,
            IS_DIFFICULT_SESSION=True  # Флаг сложной сессии
        )

        # Отображаем первое задание
        await display_task_by_id(callback.message, task_ids[0], state)
        await callback.answer()

    except Exception as e:
        logger.error(
            f"Error in handle_difficult_subtopic_selection: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при загрузке сложных заданий", show_alert=True)


@router.callback_query(F.data.startswith("answer:"))
async def handle_button_answer(callback: CallbackQuery, state: FSMContext):
    try:
        # Проверяем текущее состояние пользователя
        current_state = await state.get_state()
        if current_state != TaskStates.WAITING_ANSWER.state:
            await callback.answer("Это задание уже проверено", show_alert=True)
            return

        # Проверяем, не устарел ли callback
        try:
            await callback.answer()  # Быстрый ответ, чтобы избежать ошибки "query is too old"
        except Exception as e:
            logger.warning(f"Callback answer error (likely expired): {e}")
            return  # Просто выходим, если callback устарел

        # Разбираем данные callback
        _, task_id, answer_idx = callback.data.split(":")
        task_id = int(task_id)
        answer_idx = int(answer_idx)

        # Сразу отвечаем на callback, чтобы убрать анимацию
        await callback.answer()

        async with AsyncSessionLocal() as session:
            # Начинаем транзакцию на уровне обработчика
            async with session.begin():
                task = await session.get(Task, task_id, with_for_update=True)
                if not task:
                    await callback.answer("Задание не найдено", show_alert=True)
                    return

                # Проверяем ответ
                from core.services.answer_checker import check_answer
                result = await check_answer(
                    session=session,
                    task_id=task_id,
                    user_answer=task.answer_options[answer_idx],
                    user_id=callback.from_user.id
                )

                if "error" in result:
                    await callback.answer(result["error"], show_alert=True)
                    return

                # Обновляем состояние
                await state.set_state(TaskStates.SHOWING_RESULT)

                # Отправляем результат
                await callback.answer()
                await callback.message.answer(
                    f"{'✅ Правильно!' if result['is_correct'] else '❌ Неверно!'}",
                    reply_markup=theory_solution_kb(
                        result['task_id'],
                        result['complexity']
                    )
                )

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
                    await callback.answer("Видеоразбор отсутствует, но мы занимаемся его созданием 🎥", show_alert=True)
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
