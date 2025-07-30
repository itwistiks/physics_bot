import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.database.models import Task, Complexity
from core.fsm.states import TaskStates
from config.database import AsyncSessionLocal
from ..keyboards.inline import answer_options_kb
from ..keyboards.reply import task_navigation_kb

logger = logging.getLogger(__name__)


async def display_task(message: Message, task: Task, state: FSMContext):
    """Отображает задание с вариантами ответов"""
    try:
        # Добавляем отметку о сложности
        complexity_marker = ""
        if task.complexity == Complexity.HIGH:
            complexity_marker = "🔥 "

        text = (
            f"📌 Номер задания: {task.id} {complexity_marker}\n\n"
            f"Тип задания: {task.type_number}\n\n"
            f"{task.task_content['text']}\n\n"
        )

        # Проверяем наличие изображения
        image_url = task.task_content.get('image')
        task_text = task.task_content.get('text', 'Текст задания отсутствует')

        if image_url:
            # Если есть изображение - отправляем фото с подписью
            try:
                msg = await message.answer_photo(
                    photo=image_url,
                    caption=text,
                    reply_markup=answer_options_kb(
                        task.answer_options, task.id)
                )
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                # Если не удалось отправить фото, отправляем просто текст
                msg = await message.answer(
                    task_text + "\n\n⚠️ Не удалось загрузить изображение",
                    reply_markup=answer_options_kb(
                        task.answer_options, task.id)
                )
        else:
            # Если нет изображения - отправляем только текст
            msg = await message.answer(
                text,
                reply_markup=answer_options_kb(task.answer_options, task.id)
            )

        # Сохраняем данные в состоянии
        await state.update_data(
            task_message_id=msg.message_id,
            chat_id=message.chat.id,
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
        await message.answer(f"Произошла ошибка при отображении задания {task.id}")


async def display_task_by_id(message: Message, task_id: int, state: FSMContext):
    """Отображает задание с проверкой состояния"""
    try:
        async with AsyncSessionLocal() as session:
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
                    await message.answer("Задание не найдено")
                    return

        # Устанавливаем состояние перед отображением задания
        await state.set_state(TaskStates.WAITING_ANSWER)
        await display_task(message, task, state)

    except Exception as e:
        logger.error(f"Error in display_task_by_id: {e}", exc_info=True)
        await message.answer("Ошибка при загрузке задания")
        await state.clear()
