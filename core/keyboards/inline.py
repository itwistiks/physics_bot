from core.database.models import Complexity  # Импортируем enum сложности
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from sqlalchemy import select
from config.database import AsyncSessionLocal
from core.database.models import Task, PartNumber, Complexity


def answer_options_kb(options: list, task_id: int):
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        builder.button(text=f"{option}",
                       callback_data=f"answer:{task_id}:{i}")
    builder.adjust(1)
    return builder.as_markup()


def theory_solution_kb(task_id: int, complexity: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопка "Теория" (всегда есть)
    builder.button(text="📚 Теория", callback_data=f"theory:{task_id}")

    # Кнопка "Разбор" (только для HIGH сложности)
    if complexity == Complexity.HIGH.value:  # Проверяем, что сложность = 'high'
        builder.button(text="🎥 Разбор", callback_data=f"solution:{task_id}")

    # Располагаем кнопки вертикально (одна под другой)
    builder.adjust(1)

    return builder.as_markup()


async def part_one_types_kb():
    """Создает inline-клавиатуру с кнопками для всех типов заданий первой части"""
    builder = InlineKeyboardBuilder()

    async with AsyncSessionLocal() as session:
        async with session.begin():  # Явное управление транзакцией
            # Получаем уникальные номера типов заданий первой части
            stmt = select(Task.type_number).where(
                Task.part_number == PartNumber.PART_ONE
            ).distinct().order_by(Task.type_number)

            result = await session.execute(stmt)
            type_numbers = result.scalars().all()

            if not type_numbers:
                # Если заданий нет, возвращаем пустую клавиатуру
                return builder.as_markup()

            # Добавляем кнопки для каждого типа
            for type_num in type_numbers:
                builder.button(
                    text=str(type_num),
                    callback_data=f"part_one:{type_num}"
                )

            # Настраиваем количество кнопок в ряду (например, по 2)
            builder.adjust(2)

            return builder.as_markup()


async def part_two_types_kb():
    """Создает inline-клавиатуру с кнопками для всех типов заданий первой части"""
    builder = InlineKeyboardBuilder()

    async with AsyncSessionLocal() as session:
        async with session.begin():  # Явное управление транзакцией
            # Получаем уникальные номера типов заданий первой части
            stmt = select(Task.type_number).where(
                Task.part_number == PartNumber.PART_TWO
            ).distinct().order_by(Task.type_number)

            result = await session.execute(stmt)
            type_numbers = result.scalars().all()

            if not type_numbers:
                # Если заданий нет, возвращаем пустую клавиатуру
                return builder.as_markup()

            # Добавляем кнопки для каждого типа
            for type_num in type_numbers:
                builder.button(
                    text=str(type_num),
                    callback_data=f"part_one:{type_num}"
                )

            # Настраиваем количество кнопок в ряду (например, по 2)
            builder.adjust(2)

            return builder.as_markup()
