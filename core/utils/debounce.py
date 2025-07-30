from aiogram import types
from functools import wraps
import asyncio
from typing import Callable, Any


def throttle(rate: float = 1.0):
    def decorator(func: Callable):
        last_called = 0

        @wraps(func)
        async def wrapped(*args, **kwargs):
            nonlocal last_called
            current_time = asyncio.get_event_loop().time()

            if current_time - last_called < rate:
                if isinstance(args[0], (types.Message, types.CallbackQuery)):
                    await args[0].answer("⏳ Подождите перед повторным нажатием")
                return

            last_called = current_time
            return await func(*args, **kwargs)

        return wrapped
    return decorator
