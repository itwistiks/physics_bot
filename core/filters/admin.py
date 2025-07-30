from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy import select
from config.database import AsyncSessionLocal
from core.database.models import User, UserStatus


class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        async with AsyncSessionLocal() as session:
            user = await session.scalar(
                select(User)
                .where(User.id == message.from_user.id)
            )

            # Админами считаем пользователей со статусом ADMIN или MODERATOR
            return user is not None and (user.status == UserStatus.ADMIN or user.status == UserStatus.MODERATOR)
