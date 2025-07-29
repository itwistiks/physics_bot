from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from core.keyboards.inline import theory_solution_kb
from core.database.models import Task
import logging

logger = logging.getLogger(__name__)


async def check_answer(
    message: Message,
    task_id: int,
    user_answer: str,
    callback: CallbackQuery = None
) -> bool:
    """Оптимизированная проверка ответа с единой сессией"""
    try:
        async with AsyncSessionLocal() as session:
            # Явно начинаем транзакцию
            async with session.begin():
                task = await session.get(Task, task_id)
                if not task:
                    if callback:
                        await callback.answer("⚠️ Задание не найдено", show_alert=True)
                    return False

                is_correct = (str(user_answer).strip().lower()
                              == str(task.correct_answer).strip().lower())

                # Всплывающее уведомление
                try:
                    await message.answer(
                        "✅ Правильно!" if is_correct else "❌ Неверно!",
                        reply_markup=theory_solution_kb(task_id)
                    )
                except Exception as e:
                    logger.error(f"Callback error: {e}")

                # Возвращаем результат ДО отправки сообщения
                return is_correct

    except Exception as e:
        logger.error(f"Check answer error: {e}")
        return False
