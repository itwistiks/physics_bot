from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Any
from aiogram.types import TelegramObject
from config.database import AsyncSessionLocal
from core.services.user_service import get_or_create_user


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        # Работаем только с сообщениями от пользователей
        if not hasattr(event, 'from_user'):
            return await handler(event, data)

        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(
                session=session,
                user_id=event.from_user.id,
                username=event.from_user.username
            )
            data['user'] = user  # Добавляем пользователя в контекст

        return await handler(event, data)
