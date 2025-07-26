from config.settings import ADMIN_USER_ID, LEADS_TOKEN

from datetime import datetime, timedelta
from aiogram.fsm.storage.base import StorageKey

import aiohttp

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import or_f

from aiogram import Router, types
from aiogram.filters import Text
from core.keyboards.main_menu import (
    main_menu_kb,
    practice_menu_kb,
    cancel_kb
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
    if last_request and (datetime.now() - last_request) < timedelta(minutes=120):
        remaining = (last_request + timedelta(minutes=120)) - datetime.now()
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
        "Выберите тип практики:",
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
                    text="Перейти на сайт",
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


@router.message(Text("🔙 Назад"))
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
