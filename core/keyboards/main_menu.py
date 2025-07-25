from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder


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
    builder.button(text="👨‍🏫 Репетитор")
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


# inline menu


def part_one_types_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="1", callback_data="part_one:1")
    builder.button(text="2", callback_data="part_one:2")
    builder.button(text="3", callback_data="part_one:3")
    builder.adjust(3)
    return builder.as_markup()


def new_task_kb(task_type: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Новое задание",
                   callback_data=f"part_one:{task_type}")
    builder.button(text="🔙 К выбору типа", callback_data="part_one:back")
    return builder.as_markup()
