from config.settings import ADMIN_USER_ID, LEADS_TOKEN
from config.database import AsyncSessionLocal

from datetime import datetime, timedelta

import aiohttp

from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.context import FSMContext
from aiogram.filters import or_f, StateFilter
from aiogram import Router, types, F
from aiogram.filters import Text
from aiogram.types import Message, CallbackQuery

from core.keyboards.reply import (
    main_menu_kb,
    practice_menu_kb,
    cancel_kb,
    tasks_menu_kb
)
from core.keyboards.inline import (
    part_one_types_kb,
    answer_options_kb,
    task_navigation_kb,
    theory_solution_kb
)

from sqlalchemy import select
from sqlalchemy.orm import selectinload
import random

from core.database.models import Task, Theory

from core.services.task_service import get_random_task, prepare_task_text
from core.fsm.states import TaskStates

from core.keyboards.inline_menu import (
    theory_solution_kb,
    task_navigation_kb
)


router = Router()


# Обработка текста после нажатия "Поддержка"


user_cooldowns = {}


class SupportStates(StatesGroup):
    waiting_for_message = State()  # Состояние ожидания сообщения


@router.message(Text("✉️ Поддержка"))
async def support_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверяем кулдаун
    last_request = user_cooldowns.get(user_id)
    if last_request and (datetime.now() - last_request) < timedelta(minutes=10):
        remaining = (last_request + timedelta(minutes=10)) - datetime.now()
        await message.answer(
            f"⏳ Вы сможете отправить следующее сообщение через {remaining.seconds // 60} мин.",
            reply_markup=main_menu_kb()
        )
        return

    # Устанавливаем кулдаун
    user_cooldowns[user_id] = datetime.now()

    await state.set_state(SupportStates.waiting_for_message)
    await message.answer(
        "✍️ Напишите ваше сообщение для поддержки:",
        reply_markup=cancel_kb()
    )


@router.message(Text("❌ Отменить"))
async def cancel_support(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Отправка сообщения отменена",
        reply_markup=main_menu_kb()
    )


@router.message(SupportStates.waiting_for_message)
async def handle_support_message(message: types.Message, state: FSMContext):
    try:
        # Логируем полученное сообщение
        # print(f"🟢 Получено сообщение поддержки: {message.text}")

        # Отправляем админу
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"https://api.telegram.org/bot{LEADS_TOKEN}/sendMessage",
                json={
                    "chat_id": ADMIN_USER_ID,
                    "text": f"✉️ Письмо в поддержку \n\nТелеграм: @{message.from_user.username}\nID: {message.from_user.id}\n\n📝 Сообщение:\n{message.text}\n\n⏱️ {datetime.now()}",
                    "parse_mode": "HTML"
                }
            )

        await message.answer(
            "✅ Ваше сообщение отправлено!",
            reply_markup=main_menu_kb()
        )
        await state.clear()  # Выходим из состояния

    except Exception as e:
        print(f"🔴 Ошибка: {e}")
        await message.answer(
            "❌ Ошибка при отправке",
            reply_markup=main_menu_kb()
        )
        await state.clear()


# Обработка кнопки "Практика"


@router.message(Text("✏️ Практика"))
async def practice_menu(message: types.Message):
    await message.answer(
        "Выберите тип практики",
        reply_markup=practice_menu_kb()
    )


# Обработка кнопки "Статистика"


@router.message(Text("📊 Статистика"))
async def show_stats(message: types.Message):
    # Здесь будет логика получения статистики
    await message.answer(
        "📊 Ваша статистика:\n\n"
        "✅ Решено задач: 15\n"
        "📈 Правильных ответов: 80%\n"
        "🔥 Рекордная серия: 5 верных подряд",
        reply_markup=main_menu_kb()
    )


# Обработка кнопки "Репетитор"


@router.message(Text("👨‍🏫 Репетитор"))
async def tutor_redirect(message: types.Message):
    await message.answer(
        "Переход к репетитору:",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(
                    text="Перейти на сайт репетитора",
                    url="https://google.com"
                )
            ]]
        )
    )


# Обработка кнопки "Другие предметы"


@router.message(Text("📚 Другие предметы"))
async def other_subjects(message: types.Message):
    await message.answer(
        "Пока в разработке 🛠",
        reply_markup=main_menu_kb()
    )


# Обработка кнопки "Назад"


@router.message(Text("✏️ Назад"))
async def back_to_main(message: types.Message):
    await message.answer(
        "Выберите тип практики:",
        reply_markup=main_menu_kb()
    )


# Обработка кнопки "Отменить"


@router.message(Text("❌ Отменить"))
async def cancel_action(message: types.Message):
    await message.answer(
        "Действие отменено",
        reply_markup=main_menu_kb()
    )


@router.message(Text("📝 Задания"))
async def tasks_menu(message: types.Message):
    await message.answer(
        "Выберите тип практики:",
        reply_markup=tasks_menu_kb()
    )


# Обработчик случайных задач

async def display_task(message: Message, task: Task, state: FSMContext):
    options_text = "\n".join(
        [f"{chr(65+i)}. {option}" for i, option in enumerate(task.answer_options)])
    text = (
        f"📌 Тип задания: {task.type_number}\n\n"
        f"{task.task_content['text']}\n\n"
        f"Варианты ответов:\n{options_text}"
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


@router.message(Text("🎲 Случайные задачи"))
async def random_task(message: Message, state: FSMContext):
    task = await get_random_task()
    if not task:
        await message.answer("❌ Задачи не найдены", reply_markup=tasks_menu_kb())
        return

    await display_task(message, task, state)


# Обработчик следующего задания


@router.callback_query(F.data.startswith("next_task:"))
async def handle_next_task(callback: CallbackQuery, state: FSMContext):
    try:
        task_type = int(callback.data.split(":")[1])
        await state.update_data(current_type=task_type)

        # Загружаем задание ВМЕСТЕ с теорией
        async with AsyncSessionLocal() as session:
            stmt = select(Task).where(
                Task.type_number == task_type
            ).options(
                selectinload(Task.theory)  # Жадно загружаем теорию
            )
            tasks = (await session.execute(stmt)).scalars().all()

            if not tasks:
                await callback.answer("Задания этого типа не найдены", show_alert=True)
                return

            task = random.choice(tasks)
            await display_task(callback.message, task, state)

    except Exception as e:
        print(f"Error in next_task: {e}")
        await callback.answer("Ошибка при загрузке задания", show_alert=True)

    await callback.answer()

# Обработчик остановки практики


@router.callback_query(F.data == "stop_practice")
async def handle_stop_practice(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Практика завершена",
        reply_markup=practice_menu_kb()
    )
    await callback.answer()


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
    await callback.answer("Разбор будет здесь")


# Обработчики неактивных кнопок


@router.message(Text("📘 Вторая часть"))
async def part_two(message: types.Message):
    await message.answer(
        "Раздел в разработке 🛠",
        reply_markup=tasks_menu_kb()
    )


# Обработчик кнопки "Назад"


@router.message(Text("📝 Назад"))
async def back_to_practice(message: types.Message):
    await message.answer(
        "Выберите тип практики:",
        reply_markup=practice_menu_kb()
    )
