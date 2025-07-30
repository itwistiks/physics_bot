from config.settings import ADMIN_USER_ID, LEADS_TOKEN
from config.database import AsyncSessionLocal

from datetime import datetime, timedelta

import aiohttp

from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.context import FSMContext, Bot
from aiogram.filters import or_f, StateFilter
from aiogram import Router, types, F
from aiogram.filters import Text
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.keyboards.reply import (
    main_menu_kb,
    practice_menu_kb,
    cancel_kb,
    tasks_menu_kb,
    task_navigation_kb
)
from core.keyboards.inline import (
    part_one_types_kb,
    part_two_types_kb,
    answer_options_kb,
    theory_solution_kb
)

from sqlalchemy import select
from sqlalchemy.orm import selectinload
import random

from core.database.models import Task, Theory

from core.fsm.states import TaskStates

from core.services.task_display import display_task, display_task_by_id
from core.services.task_utils import get_shuffled_task_ids
# from core.services.answer_processing import process_answer
from core.services.task_utils import get_random_task
from core.services.answer_checker import check_answer
from core.services.stats_service import update_user_stats

import logging


logger = logging.getLogger(__name__)


router = Router()


# # # # # # # # # # # # # # # # # # # # # # # # # # # #
'''ГЛАВНОЕ МЕНЮ'''
# # # # # # # # # # # # # # # # # # # # # # # # # # # #


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


# # # # # # # # # # # # # # # # # # # # # # # # # # # #
'''ПРАКТИКА МЕНЮ'''
# # # # # # # # # # # # # # # # # # # # # # # # # # # #


# Обработчик кнопки "Задания"


@router.message(Text("📝 Задания"))
async def tasks_menu(message: types.Message):
    await message.answer(
        "Выберите тип практики:",
        reply_markup=tasks_menu_kb()
    )


# Обработчик кнопки "Вариант"


@router.message(Text("📋 Вариант"))
async def other_subjects(message: types.Message):
    await message.answer(
        "Пока в разработке 🛠",
        reply_markup=main_menu_kb()
    )


# Обработчик кнопки "Темы"


@router.message(Text("📖 Темы"))
async def other_subjects(message: types.Message):
    await message.answer(
        "Пока в разработке 🛠",
        reply_markup=main_menu_kb()
    )


# Обработчик кнопки "Сложные задачи"


@router.message(Text("🔥 Сложные задачи"))
async def other_subjects(message: types.Message):
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


# Обработчик кнопки "Назад"


@router.message(Text("✏️ Назад"))
async def back_to_main(message: types.Message):
    await message.answer(
        "Выберите тип практики:",
        reply_markup=main_menu_kb()
    )


# # # # # # # # # # # # # # # # # # # # # # # # # # # #
'''ЗАДАНИЕ МЕНЮ'''
# # # # # # # # # # # # # # # # # # # # # # # # # # # #


# Обработчик кнопки "Случайные задачи"


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


# Обработчик кнопки "Первая часть"

@router.message(Text("📋 Первая часть"))
async def show_part_one_menu(message: Message):
    kb = await part_one_types_kb()
    await message.answer(
        "Выберите тип задания первой части:",
        reply_markup=kb
    )

# Обработчик кнопки "Вторая часть"


@router.message(Text("📘 Вторая часть"))
async def show_part_one_menu(message: Message):
    kb = await part_two_types_kb()
    await message.answer(
        "Выберите тип задания второй части:",
        reply_markup=kb
    )


# Обработчик кнопки "Назад"


@router.message(Text("📝 Назад"))
async def back_to_practice(message: types.Message):
    await message.answer(
        "Выберите тип практики:",
        reply_markup=practice_menu_kb()
    )


# -------------| Обработчики reply-кнопок задачи |------------- #


# Обработчик следующего задания


@router.message(Text("▶️ Следующее задание"))
async def next_task(message: Message, state: FSMContext, bot: Bot):  # Добавляем Bot в параметры
    try:
        data = await state.get_data()
        task_ids = data.get('TASK_LIST', [])
        current_idx = data.get('CURRENT_INDEX', 0)
        task_message_id = data.get('task_message_id')
        chat_id = data.get('chat_id', message.chat.id)

        print(
            f"DEBUG: Trying to delete message {task_message_id} in chat {chat_id}")

        # Удаляем предыдущее сообщение
        if task_message_id:
            try:
                await bot.delete_message(  # Используем bot из параметров
                    chat_id=chat_id,
                    message_id=task_message_id
                )
                print("DEBUG: Message deleted successfully")
            except Exception as e:
                print(f"DEBUG: Failed to delete message: {e}")

        if not task_ids:
            await message.answer("❌ Список заданий пуст", reply_markup=practice_menu_kb())
            await state.clear()
            return

        if current_idx + 1 >= len(task_ids):
            await message.answer("🎉 Вы завершили все задания в этой сессии!", reply_markup=practice_menu_kb())
            await state.clear()
            return

        next_idx = current_idx + 1
        await display_task_by_id(message, task_ids[next_idx], state)
        await state.update_data(CURRENT_INDEX=next_idx)

    except Exception as e:
        logger.error(f"Error in next_task: {e}", exc_info=True)
        await message.answer("⚠️ Ошибка загрузки следующего задания", reply_markup=practice_menu_kb())
        await state.clear()


# Обработчик остановки практики


@router.message(Text("⏹ Остановиться"))
async def stop_practice(message: Message, state: FSMContext, bot: Bot):  # Добавляем Bot
    data = await state.get_data()
    task_message_id = data.get('task_message_id')
    chat_id = data.get('chat_id', message.chat.id)

    if task_message_id:
        try:
            await bot.delete_message(  # Используем bot из параметров
                chat_id=chat_id,
                message_id=task_message_id
            )
        except Exception as e:
            logger.warning(f"Could not delete message: {e}")

    # Очищаем текущее состояние, чтобы не ждать ответа
    await state.clear()

    await message.answer(
        "Практика завершена",
        reply_markup=practice_menu_kb()
    )


# Обработчик текста


@router.message(F.text, StateFilter(TaskStates.WAITING_ANSWER))
async def handle_text_answer(message: Message, state: FSMContext):
    """Обработчик текстовых ответов с сохранением check_answer()"""
    try:
        data = await state.get_data()
        task_id = data['current_task_id']

        async with AsyncSessionLocal() as session:
            async with session.begin():
                await check_answer(
                    session=session,
                    message=message,
                    task_id=task_id,
                    user_answer=message.text,
                    state=state
                )

    except Exception as e:
        logger.error(f"Ошибка обработки: {str(e)}", exc_info=True)
        await message.answer("⚠️ Ошибка при проверке ответа")
        await state.clear()
