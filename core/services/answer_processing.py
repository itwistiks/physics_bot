# from aiogram.types import Message
# from aiogram.fsm.context import FSMContext
# from aiogram.types import Message, CallbackQuery
# from sqlalchemy.orm import selectinload

# from config.database import AsyncSessionLocal
# from core.database.models import Task
# from core.keyboards.inline import theory_solution_kb
# from core.services.stats_service import update_user_stats

# import logging

# logger = logging.getLogger(__name__)


# async def process_answer(message: Message, task_id: int, user_answer: str, state: FSMContext, callback: CallbackQuery = None):
#     """Надёжная обработка ответа с правильным выводом результата"""
#     try:
#         async with AsyncSessionLocal() as session:
#             # Загружаем задание с нужными связями
#             task = await session.get(
#                 Task,
#                 task_id,
#                 options=[
#                     selectinload(Task.topic),
#                     selectinload(Task.subtopic)
#                 ]
#             )

#             if not task:
#                 if callback:
#                     await callback.answer("Задание не найдено", show_alert=True)
#                 return False

#             # Проверяем ответ
#             is_correct = str(user_answer).strip().lower() == str(
#                 task.correct_answer).strip().lower()

#             # Обновляем статистику
#             try:
#                 await update_user_stats(session, message.from_user.id, task_id, is_correct)
#             except Exception as e:
#                 logger.error(f"Stats update failed: {e}")
#                 if callback:
#                     await callback.answer("⚠️ Ошибка сохранения статистики", show_alert=True)

#             # Выводим результат
#             if callback:
#                 await callback.answer(
#                     "✅ Правильно!" if is_correct else "❌ Неверно!",
#                     show_alert=True
#                 )

#             # Отправляем правильный ответ
#             await message.answer(
#                 f"📌 Правильный ответ: {task.correct_answer}\n"
#                 f"💡 Объяснение: {task.explanation or 'Объяснение отсутствует'}",
#                 reply_markup=theory_solution_kb(task_id)
#             )

#             await state.update_data(
#                 last_answer_correct=is_correct,
#                 waiting_for_answer=False
#             )
#             return True

#     except Exception as e:
#         logger.error(f"Error in process_answer: {e}")
#         if callback:
#             await callback.answer("⚠️ Ошибка проверки", show_alert=True)
#         return False
