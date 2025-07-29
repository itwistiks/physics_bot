import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.database.models import Task
from core.fsm.states import TaskStates
from config.database import AsyncSessionLocal
from ..keyboards.inline import answer_options_kb
from ..keyboards.reply import task_navigation_kb

logger = logging.getLogger(__name__)


async def display_task(message: Message, task: Task, state: FSMContext):
    """Отображает задание с вариантами ответов"""
    try:
        # Формируем текст задания
        options_text = "\n".join(
            f"{chr(65+i)}. {option}"
            for i, option in enumerate(task.answer_options)
        )

        text = (
            f"📌 Номер задания: {task.id}\n\n"
            f"Тип задания: {task.type_number}\n\n"
            f"{task.task_content['text']}\n\n"
        )

        # Отправляем задание с фото или без
        if task.task_content.get('image'):
            msg = await message.answer_photo(
                photo=task.task_content['image'],
                caption=text,
                reply_markup=answer_options_kb(task.answer_options, task.id)
            )
        else:
            msg = await message.answer(
                text,
                reply_markup=answer_options_kb(task.answer_options, task.id)
            )

        # Сохраняем данные в состоянии
        await state.update_data(
            task_message_id=msg.message_id,
            current_task_id=task.id,
            current_type=task.type_number
        )

        # Отправляем клавиатуру навигации
        await message.answer(
            "Выберите действие:",
            reply_markup=task_navigation_kb(task.type_number)
        )

        await state.set_state(TaskStates.WAITING_ANSWER)
        await state.update_data(current_task_id=task.id)
        logger.info(
            f"Установлено состояние WAITING_ANSWER для задания {task.id}")

    except Exception as e:
        logger.error(f"Error displaying task: {str(e)}")
        await message.answer("Произошла ошибка при отображении задания")


async def display_task_by_id(message: Message, task_id: int, state: FSMContext):
    """Новая версия с защитой от неявных ROLLBACK"""
    try:
        logger.info(f"Starting task display for ID: {task_id}")

        async with AsyncSessionLocal() as session:
            # Явно контролируем транзакцию
            async with session.begin():
                task = await session.get(
                    Task,
                    task_id,
                    options=[
                        selectinload(Task.topic),
                        selectinload(Task.subtopic)
                    ]
                )

                if not task:
                    logger.error(f"Task {task_id} not found")
                    await message.answer("Задание не найдено")
                    return

                # Явно фиксируем перед отображением
                await session.commit()

        # Отображение вне сессии
        await display_task(message, task, state)

    except Exception as e:
        logger.error(
            f"Critical error in display_task_by_id: {e}", exc_info=True)
        await message.answer("Ошибка при загрузке задания")
