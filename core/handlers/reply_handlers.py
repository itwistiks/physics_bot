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
    tasks_menu_kb,
    task_navigation_kb
)
from core.keyboards.inline import (
    part_one_types_kb,
    answer_options_kb,
    theory_solution_kb
)

from sqlalchemy import select
from sqlalchemy.orm import selectinload
import random

from core.database.models import Task, Theory

from core.services.task_utils import get_random_task
from core.fsm.states import TaskStates
from core.services.task_display import display_task, display_task_by_id
from core.services.task_utils import get_shuffled_task_ids


router = Router()


# Обработчик текста после нажатия "Поддержка" и антиспам


user_cooldowns = {}

# Время до возможности написать следующее сообщение в поддержку
time_stop = 10


class SupportStates(StatesGroup):
    waiting_for_message = State()  # Состояние ожидания сообщения


@router.message(Text("✉️ Поддержка"))
async def support_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверяем кулдаун
    last_request = user_cooldowns.get(user_id)
    if last_request and (datetime.now() - last_request) < timedelta(minutes=time_stop):
        remaining = (last_request + timedelta(minutes=time_stop)
                     ) - datetime.now()
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

# Обработчик если передумали писать в поддержку


@router.message(Text("❌ Отменить"))
async def cancel_support(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Отправка сообщения отменена",
        reply_markup=main_menu_kb()
    )

# Обработчик отправления сообщения в поддержку


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


# Обработчик кнопки "Практика"


@router.message(Text("✏️ Практика"))
async def practice_menu(message: types.Message):
    await message.answer(
        "Выберите тип практики",
        reply_markup=practice_menu_kb()
    )


# Обработчик кнопки "Статистика"


@router.message(Text("📊 Статистика"))
async def show_stats(message: types.Message):
    # Здесь будет логика получения статистики
    await message.answer(
        "Пока в разработке 🛠",
        reply_markup=main_menu_kb()
    )


# Обработчик кнопки "Репетитор"


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


# Обработчик кнопки "Другие предметы"


@router.message(Text("📚 Другие предметы"))
async def other_subjects(message: types.Message):
    await message.answer(
        "Пока в разработке 🛠",
        reply_markup=main_menu_kb()
    )


# Обработчик кнопки "Назад"


@router.message(Text("✏️ Назад"))
async def back_to_main(message: types.Message):
    await message.answer(
        "Выберите тип практики:",
        reply_markup=main_menu_kb()
    )


# Обработчик кнопки "Отменить"


@router.message(Text("❌ Отменить"))
async def cancel_action(message: types.Message):
    await message.answer(
        "Действие отменено",
        reply_markup=main_menu_kb()
    )


# Обработчик кнопки "Задания"


@router.message(Text("📝 Задания"))
async def tasks_menu(message: types.Message):
    await message.answer(
        "Выберите тип практики:",
        reply_markup=tasks_menu_kb()
    )


# Обработчик случайных задач


@router.message(Text("🎲 Случайные задачи"))
async def random_tasks(message: Message, state: FSMContext):
    # Получаем перемешанные ID заданий ВСЕХ типов
    task_ids = await get_shuffled_task_ids()

    if not task_ids:
        await message.answer("❌ Задачи не найдены", reply_markup=tasks_menu_kb())
        return

    await state.update_data(
        TASK_LIST=task_ids,
        CURRENT_INDEX=0,
        IS_RANDOM_SESSION=True  # Флаг, что это случайная сессия
    )

    await display_task_by_id(message, task_ids[0], state)


# Обработчики неактивных кнопок

@router.message(Text("📋 Первая часть"))
async def show_part_one_menu(message: Message):
    await message.answer(
        "Выберите тип задания первой части:",
        reply_markup=part_one_types_kb()
    )


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


# -------------| Шаблон вывода задания |------------- #
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
    await callback.answer("Разбор будет здесь позже")

    # reply_handlers.py


@router.message(Text("▶️ Следующее задание"), StateFilter(TaskStates.SHOWING_RESULT))
async def next_task(message: Message, state: FSMContext):
    data = await state.get_data()
    task_ids = data.get('TASK_LIST', [])
    current_index = data.get('CURRENT_INDEX', 0)

    if not task_ids:
        await message.answer("❌ Список заданий пуст")
        return

    # Если это последнее задание в сессии
    if current_index >= len(task_ids) - 1:
        if data.get('IS_RANDOM_SESSION', True):
            # Для случайной сессии - получаем новые случайные задания
            new_task_ids = await get_shuffled_task_ids()
        else:
            # Для сессии по типу - начинаем сначала
            new_task_ids = await get_shuffled_task_ids(
                task_type=data.get('current_type')
            )

        if not new_task_ids:
            await message.answer("❌ Не удалось загрузить новые задания")
            return

        await state.update_data(
            TASK_LIST=new_task_ids,
            CURRENT_INDEX=0
        )
        await display_task_by_id(message, new_task_ids[0], state)
    else:
        # Показываем следующее задание из текущего списка
        new_index = current_index + 1
        await state.update_data(CURRENT_INDEX=new_index)
        await display_task_by_id(message, task_ids[new_index], state)


@router.message(Text("⏹ Остановиться"))
async def stop_practice(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Практика завершена",
        reply_markup=practice_menu_kb()
    )
