from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ..keyboards.inline import answer_options_kb
from ..keyboards.reply import task_navigation_kb

from core.fsm.states import TaskStates
from core.database.models import Task
from config.database import AsyncSessionLocal


async def display_task(message: Message, task: Task, state: FSMContext):
    options_text = "\n".join(
        f"{chr(65+i)}. {option}" for i, option in enumerate(task.answer_options))
    text = (
        f"📌 Номет задания: {task.id}\n\n"
        f"Тип задания: {task.type_number}\n\n"
        f"{task.task_content['text']}\n\n"
    )

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

    await state.update_data(
        task_message_id=msg.message_id,
        current_task_id=task.id,
        current_type=task.type_number
    )
    await state.set_state(TaskStates.WAITING_ANSWER)

    await message.answer(
        "Выберите действие:",
        reply_markup=task_navigation_kb(task.type_number)
    )


async def display_task_by_id(message: Message, task_id: int, state: FSMContext):
    """Отображает задание по его ID"""
    async with AsyncSessionLocal() as session:
        task = await session.get(Task, task_id)
        if not task:
            await message.answer("Задание не найдено")
            return

        await display_task(message, task, state)
