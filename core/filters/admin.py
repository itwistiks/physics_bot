from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy import select
from config.database import AsyncSessionLocal
from core.database.models import User, UserStatus


class IsTeacherFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        async with AsyncSessionLocal() as session:
            user = await session.scalar(
                select(User)
                .where(User.id == message.from_user.id)
            )

            return user is not None and (user.status == UserStatus.ADMIN or user.status == UserStatus.MODERATOR or user.status == UserStatus.TEACHER)


class IsModeratorFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        async with AsyncSessionLocal() as session:
            user = await session.scalar(
                select(User)
                .where(User.id == message.from_user.id)
            )

            return user is not None and (user.status == UserStatus.ADMIN or user.status == UserStatus.MODERATOR)


class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        async with AsyncSessionLocal() as session:
            user = await session.scalar(
                select(User)
                .where(User.id == message.from_user.id)
            )

            return user is not None and (user.status == UserStatus.ADMIN)
