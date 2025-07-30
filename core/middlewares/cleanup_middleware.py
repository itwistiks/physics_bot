from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Awaitable, Any, Dict
from aiogram.fsm.context import FSMContext
import logging

logger = logging.getLogger(__name__)


class CleanupMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Работаем только с сообщениями
        if not isinstance(event, Message):
            return await handler(event, data)

        # Получаем состояние и FSMContext
        state: FSMContext = data.get('state')
        if not state:
            return await handler(event, data)

        # Получаем сохраненные данные о предыдущих сообщениях
        state_data = await state.get_data()
        buttons_message_id = state_data.get('buttons_message_id')
        chat_id = state_data.get('chat_id')

        # Если есть сообщение с кнопками - удаляем его
        if buttons_message_id and chat_id:
            try:
                await event.bot.delete_message(
                    chat_id=chat_id,
                    message_id=buttons_message_id
                )
                logger.debug(f"Deleted buttons message {buttons_message_id}")
            except Exception as e:
                logger.debug(f"Could not delete buttons message: {e}")

        # Вызываем следующий обработчик
        return await handler(event, data)
