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
