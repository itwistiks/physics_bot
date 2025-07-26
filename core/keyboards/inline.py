from aiogram.utils.keyboard import InlineKeyboardBuilder


def part_one_types_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="1", callback_data="part_one:1")
    builder.button(text="2", callback_data="part_one:2")
    builder.button(text="3", callback_data="part_one:3")
    builder.adjust(3)
    return builder.as_markup()


def answer_options_kb(options: list, task_id: int):
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        builder.button(text=f"{chr(65+i)}. {option}",
                       callback_data=f"answer:{task_id}:{i}")
    builder.adjust(1)
    return builder.as_markup()


def task_navigation_kb(task_type: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Следующее задание",
                   callback_data=f"next_task:{task_type}")
    builder.button(text="⏹ Остановиться", callback_data="stop_practice")
    return builder.as_markup()


def theory_solution_kb(task_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Теория", callback_data=f"theory:{task_id}")
    builder.button(text="📝 Разбор", callback_data=f"solution:{task_id}")
    return builder.as_markup()
