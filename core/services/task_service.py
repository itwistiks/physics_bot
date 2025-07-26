from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import random
from config.database import AsyncSessionLocal
from core.database.models import Task, Theory
from core.keyboards.inline_menu import (
    answer_options_kb,
    task_navigation_kb,
    theory_solution_kb
)
from core.keyboards.main_menu import practice_menu_kb
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup

from core.fsm.states import TaskStates


async def prepare_task_text(task: Task) -> str:
    """
    Формирует текст задания для отправки пользователю
    :param task: Объект задания
    :return: Отформатированная строка с заданием
    """
    options = "\n".join(f"• {opt}" for opt in task.answer_options)
    return (
        f"📌 <b>Задача #{task.id}</b>\n"
        f"🔢 Тип: {task.type_number}\n\n"
        f"{task.task_content['text']}\n\n"
        f"<i>Варианты:</i>\n{options}"
    )


async def get_random_task(task_type: int = None) -> Task:
    """
    Получает случайное задание из базы данных
    :param task_type: Если указан, возвращает задание только этого типа
    :return: Объект Task или None если задания не найдены
    """
    async with AsyncSessionLocal() as session:
        stmt = select(Task)

        if task_type is not None:
            stmt = stmt.where(Task.type_number == task_type)

        stmt = stmt.options(selectinload(Task.topic))
        tasks = (await session.execute(stmt)).scalars().all()
        return random.choice(tasks) if tasks else None


async def display_task(message: Message, task: Task, state: FSMContext):
    # Формируем текст задачи с вариантами ответов
    options_text = "\n".join(
        [f"{chr(65+i)}. {option}" for i, option in enumerate(task.answer_options)])
    text = (
        f"📌 Тип задания: {task.type_number}\n\n"
        f"{task.task_content['text']}\n\n"
        f"Варианты ответов:\n{options_text}"
    )

    # Если есть картинка
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
        current_task_id=task.id,  # Сохраняем ID текущего задания
        current_type=task.type_number,
        current_task=task  # Сохраняем весь объект задания
    )
    await state.set_state(TaskStates.WAITING_ANSWER)

    # Добавляем клавиатуру навигации
    await message.answer(
        "Выберите действие:",
        reply_markup=task_navigation_kb(task.type_number)
    )


async def check_answer(callback: CallbackQuery, task_id: int, answer_idx: int) -> bool:
    """
    Проверяет правильность ответа
    :param callback: Объект callback
    :param task_id: ID задания
    :param answer_idx: Индекс выбранного ответа
    :return: True если ответ правильный, False если нет
    """
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

        # Показываем правильный ответ
        await callback.message.answer(
            f"Правильный ответ: {task.correct_answer}",
            reply_markup=theory_solution_kb(task.id)
        )

        return is_correct


async def show_task_theory(callback: CallbackQuery, task_id: int):
    """
    Показывает теорию для задания
    :param callback: Объект callback
    :param task_id: ID задания
    """
    async with AsyncSessionLocal() as session:
        stmt = select(Task).where(Task.id == task_id).options(
            selectinload(Task.theory))
        task = (await session.execute(stmt)).scalar_one_or_none()

        if not task:
            await callback.message.answer("⚠️ Задание не найдено")
            return

        if task.theory:
            await callback.message.answer(
                f"📚 Теория по заданию {task.type_number}:\n\n{task.theory.content}",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                f"⚠️ Для задания {task.type_number} теория не найдена"
            )


async def show_task_solution(callback: CallbackQuery, task_id: int):
    """
    Показывает разбор задания
    :param callback: Объект callback
    :param task_id: ID задания
    """
    async with AsyncSessionLocal() as session:
        task = await session.get(Task, task_id)
        if task:
            await callback.message.answer(
                f"📝 Разбор задания {task.type_number}:\n\n"
                f"Правильный ответ: {task.correct_answer}\n"
                f"Объяснение: {task.solution or 'Разбор пока отсутствует'}"
            )
        else:
            await callback.message.answer("Задание не найдено")


async def cleanup_previous_task(message: Message, state: FSMContext):
    """
    Удаляет предыдущее сообщение с заданием
    :param message: Объект сообщения
    :param state: Состояние FSM
    """
    data = await state.get_data()
    if 'task_message_id' in data:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=data['task_message_id']
            )
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")


async def stop_practice_session(message: Message, state: FSMContext):
    """
    Завершает сессию практики
    :param message: Объект сообщения
    :param state: Состояние FSM
    """
    await state.clear()
    await message.answer(
        "Практика завершена",
        reply_markup=practice_menu_kb()
    ), CallbackQuery
