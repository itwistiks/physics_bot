import asyncio
from datetime import datetime
from aiogram import Bot
from config.database import AsyncSessionLocal
from core.services.reminder_service import check_inactive_users, get_reminder_text
import logging
import warnings
from sqlalchemy import exc as sa_exc

warnings.filterwarnings("ignore", category=sa_exc.SAWarning)

logger = logging.getLogger(__name__)


async def send_inactivity_reminders(bot: Bot):
    """Отправляет напоминания неактивным пользователям"""
    async with AsyncSessionLocal() as session:
        try:
            users = await check_inactive_users(session)

            for user in users:
                try:
                    reminder_text = await get_reminder_text(session, 'inactive')
                    await bot.send_message(
                        chat_id=user.id,
                        text=reminder_text
                    )

                    # Обновляем время последнего напоминания
                    user.last_interaction_time = datetime.utcnow()
                    session.add(user)

                except Exception as e:
                    logger.error(f"Error sending to {user.id}: {e}")

            await session.commit()

        except Exception as e:
            logger.error(f"Reminder system error: {e}")
            await session.rollback()
