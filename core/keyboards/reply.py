# Может стоит сделать builder.adjust(3)
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="✏️ Практика")
    builder.button(text="📊 Статистика")
    builder.button(text="👨‍🏫 Репетитор")
    builder.button(text="📚 Другие предметы")
    builder.button(text="✉️ Поддержка")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def practice_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Задания")
    builder.button(text="📋 Вариант")
    builder.button(text="📖 Темы")
    builder.button(text="🔥 Сложные задачи")
    builder.button(text="👨‍🏫 Подписка")
    builder.button(text="✏️ Назад")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отменить")
    return builder.as_markup(resize_keyboard=True)


def tasks_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎲 Случайные задачи")
    builder.button(text="📋 Первая часть")
    builder.button(text="📘 Вторая часть")
    builder.button(text="📝 Назад")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def task_navigation_kb(task_type: int):
    builder = ReplyKeyboardBuilder()
    builder.button(text="▶️ Следующее задание")
    builder.button(text="⏹ Остановиться")
    return builder.as_markup(resize_keyboard=True)
