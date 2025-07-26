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
from core.keyboards.inline_menu import (
    part_one_types_kb,
    answer_options_kb,
    task_navigation_kb,
    theory_solution_kb
)
from core.keyboards.main_menu import practice_menu_kb

router = Router()

# Состояния для FSM


class TaskStates(StatesGroup):
    WAITING_ANSWER = State()
    SHOWING_RESULT = State()


@router.message(Text("📋 Первая часть"))
async def show_part_one_menu(message: Message):
    await message.answer(
        "Выберите тип задания первой части:",
        reply_markup=part_one_types_kb()
    )


@router.callback_query(F.data.startswith("part_one:"))
async def handle_task_type(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    task_type = int(callback.data.split(":")[1])
    await state.update_data(current_type=task_type)
    await show_random_task(callback.message, task_type, state)
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

    await state.update_data(task_message_id=msg.message_id)
    await state.set_state(TaskStates.WAITING_ANSWER)
    await message.answer(
        "Выберите действие:",
        reply_markup=task_navigation_kb(task.type_number)
    )


@router.callback_query(F.data.startswith("answer:"), StateFilter(TaskStates.WAITING_ANSWER))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    _, task_id, answer_idx = callback.data.split(":")
    answer_idx = int(answer_idx)

    async with AsyncSessionLocal() as session:
        task = await session.get(Task, int(task_id))
        if not task:
            await callback.answer("Задание не найдено", show_alert=True)
            return

        # Проверяем ответ
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

    await state.set_state(TaskStates.SHOWING_RESULT)


@router.message(Text("▶️ Следующее задание"), StateFilter(TaskStates.SHOWING_RESULT))
async def next_task(message: Message, state: FSMContext):
    data = await state.get_data()
    task_type = data.get('current_type')

    # Удаляем предыдущие сообщения
    try:
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=data.get('task_message_id')
        )
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    if task_type:
        await show_random_task(message, task_type, state)
    else:
        await message.answer("Не удалось определить тип задания")


@router.message(Text("⏹ Остановиться"))
async def stop_practice(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Практика завершена",
        reply_markup=practice_menu_kb()
    )


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


@router.callback_query(F.data.startswith("solution:"))
async def show_solution(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])

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

    await callback.answer()
