import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from aiogram import Bot
from sqlalchemy import select, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.models import User, Reminder, UserStatus
from config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.check_interval = 3600  # Интервал в секундах (1 час)
        self.REMINDER_INTERVALS = {
            'promo': [1, 2, 24, 48, 72],  # часы (1, 2 - убрать)
            'inactive': [120, 168, 240, 504, 720]  # часы
        }

    async def get_users_for_reminders(self, session: AsyncSession) -> Dict[str, List[Tuple[int, str]]]:
        """Возвращает пользователей для напоминаний, сгруппированных по типу"""
        users = {'promo': [], 'inactive': []}
        current_time = datetime.utcnow()

        stmt = select(User.id, User.username, User.last_interaction_time).where(
            and_(
                not_(User.status.in_([
                    UserStatus.ADMIN.value,
                    UserStatus.MODERATOR.value,
                    UserStatus.TEACHER.value
                ])),
                User.last_interaction_time.is_not(None)
            )
        )

        result = await session.execute(stmt)

        for user_id, username, last_interaction in result.all():
            inactive_hours = (
                current_time - last_interaction).total_seconds() / 3600

            for reminder_type, intervals in self.REMINDER_INTERVALS.items():
                for interval in intervals:
                    if abs(inactive_hours - interval) <= 1:  # допуск ±1 час
                        users[reminder_type].append((user_id, username))
                        break

        return users

    async def get_reminder_text(self, session: AsyncSession, reminder_type: str) -> Optional[str]:
        """Получает текст напоминания из БД"""
        try:
            stmt = select(Reminder.text).where(
                Reminder.reminder_type == reminder_type
            ).order_by(Reminder.date.desc()).limit(1)

            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting reminder text: {e}")
            return None

    async def send_reminders(self) -> Dict[str, int]:
        """Основной метод для отправки напоминаний"""
        results = {'promo': 0, 'inactive': 0}

        async with AsyncSessionLocal() as session:
            users = await self.get_users_for_reminders(session)

            for reminder_type, user_list in users.items():
                text = await self.get_reminder_text(session, reminder_type) or self.get_default_text(reminder_type)

                for user_id, username in user_list:
                    try:
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=text
                        )
                        results[reminder_type] += 1
                        logger.info(
                            f"Sent {reminder_type} reminder to {username} ({user_id})")
                    except Exception as e:
                        logger.error(f"Failed to send to {user_id}: {e}")

        return results

    @staticmethod
    def get_default_text(reminder_type: str) -> str:
        """Тексты по умолчанию"""
        return {
            'promo': "📢 Не забудьте потренироваться сегодня! Регулярные занятия - залог успеха!",
            'inactive': "📢 Давно не виделись! Вернитесь к практике сегодня!"
        }.get(reminder_type, "Не забывайте тренироваться каждый день!")


async def send_inactivity_reminders(bot: Bot) -> Dict[str, int]:
    """Функция для прямого импорта из других модулей"""
    service = ReminderService(bot)
    return await service.send_reminders()
