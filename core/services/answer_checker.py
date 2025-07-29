from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from core.keyboards.inline import theory_solution_kb
from core.database.models import Task
from sqlalchemy import select
from core.fsm.states import TaskStates
import logging

logger = logging.getLogger(__name__)


async def check_answer(
    *,
    session: AsyncSession,
    message: Message | None = None,
    callback: CallbackQuery | None = None,
    task_id: int,
    user_answer: str,
    state: FSMContext
) -> bool:
    """Универсальная функция обработки ответа на задание"""
    try:
        # Получаем задание с блокировкой
        task = await session.execute(
            select(Task)
            .where(Task.id == task_id)
            .with_for_update()
        )
        task = task.scalar_one_or_none()

        if not task:
            if callback:
                await callback.answer("⚠️ Задание не найдено", show_alert=True)
            elif message:
                await message.answer("Задание не найдено")
            return False

        # Проверяем правильность ответа
        is_correct = str(user_answer).strip().lower() == str(
            task.correct_answer).strip().lower()

        # Формируем результат
        result_text = (
            f"{'✅ Правильно!' if is_correct else '❌ Неверно!'}"
        )

        # Обрабатываем в зависимости от типа ответа
        if callback:
            # Для inline-кнопок
            await callback.answer(
                "✅ Правильно!" if is_correct else "❌ Неверно!",
                show_alert=False
            )
            await callback.message.answer(
                result_text,
                reply_markup=theory_solution_kb(task.id, task.complexity.value)
            )
        elif message:
            # Для текстовых ответов
            await message.answer(
                result_text,
                reply_markup=theory_solution_kb(task.id, task.complexity.value)
            )

        # Обновляем состояние
        await state.set_state(TaskStates.SHOWING_RESULT)

        return is_correct

    except Exception as e:
        logger.error(f"Error processing answer: {e}", exc_info=True)
        if callback:
            await callback.answer("Произошла ошибка", show_alert=True)
        elif message:
            await message.answer("⚠️ Ошибка при проверке ответа")
        return False
