import logging
from datetime import datetime, timedelta
from aiogram import Bot
from sqlalchemy import select, and_, not_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.models import User, Reminder
from config.database import AsyncSessionLocal
from aiogram.exceptions import TelegramNetworkError
import asyncio

logger = logging.getLogger(__name__)


async def send_daily_reminders(bot: Bot):
    """Отправляет напоминания в зависимости от времени неактивности"""
    async with AsyncSessionLocal() as session:
        try:
            users = await get_users_for_reminders(session)

            # Отправляем promo (24ч)
            for user_id, username in users['promo']:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text="📢 Не забудьте потренироваться сегодня! Начните с 5 задач для лучшего результата."
                    )
                    logger.info(
                        f"Sent promo reminder to {username} ({user_id})")
                except Exception as e:
                    logger.error(f"Error sending promo to {user_id}: {e}")

            # Отправляем inactive (96ч)
            for user_id, username in users['inactive']:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text="📢 Давно не решали задачи! Вернитесь к практике сегодня!"
                    )
                    logger.info(
                        f"Sent inactive reminder to {username} ({user_id})")
                except Exception as e:
                    logger.error(f"Error sending inactive to {user_id}: {e}")

            await session.commit()
        except Exception as e:
            logger.error(f"Error in reminder system: {e}")
            await session.rollback()


async def get_users_for_reminders(session: AsyncSession):
    """Новая оптимизированная версия"""
    logger.info("Starting reminder check at %s", datetime.now())
    users = await get_users_for_reminders(session)
    logger.info("Found %d users for reminders", len(users))
    for user_id, username, status, last_active in users:
        logger.debug("Processing user %s (last active: %s)",
                     username, last_active)

    now = datetime.utcnow()
    stmt = select(
        User.id,
        User.username,
        User.status,
        User.last_interaction_time
    ).where(
        and_(
            User.status.in_(['no_sub', 'sub']),
            or_(
                and_(  # Для promo (24 часа)
                    User.last_interaction_time < now - timedelta(hours=24),
                    User.last_interaction_time >= now - timedelta(hours=96)
                ),
                and_(  # Для inactive (96 часов)
                    User.last_interaction_time < now - timedelta(hours=96)
                )
            )
        )
    ).execution_options(stream_results=True)

    result = await session.execute(stmt)
    return result.all()


async def get_reminder_text(session: AsyncSession, reminder_type: str) -> str:
    """Получает текст напоминания из базы или возвращает default"""
    try:
        reminder = await session.execute(
            select(Reminder.text)
            .where(Reminder.reminder_type == reminder_type)
            .order_by(Reminder.date.desc())
            .limit(1)
        )
        return reminder.scalar_one_or_none() or get_default_reminder(reminder_type)
    except Exception as e:
        logger.error(f"Error getting reminder text: {e}")
        return get_default_reminder(reminder_type)


def get_default_reminder(reminder_type: str) -> str:
    """Тексты по умолчанию"""
    return {
        'inactive': "📢 Давно не решали задачи! Вернитесь к практике сегодня!",
        'promo': "📢 Не забудьте потренироваться сегодня! Начните с 5 задач для лучшего результата.",
        'holiday': "🎉 Поздравляем с праздником! Отличный день для обучения!"
    }.get(reminder_type, "Не забывайте тренироваться каждый день!")


async def check_inactive_users(session: AsyncSession):
    """Проверяет неактивных пользователей за последние 24 часа"""
    from config.settings import REMINDER_INTERVAL_MINUTES, MIN_REMINDER_GAP
    inactive_threshold = datetime.utcnow() - timedelta(minutes=MIN_REMINDER_GAP)
    # inactive_threshold = datetime.utcnow() - timedelta(hours=24)

    stmt = select(User).where(
        and_(
            User.last_interaction_time < inactive_threshold,
            or_(
                User.last_interaction_time.is_(None),
                User.last_interaction_time < inactive_threshold
            ),
            User.status.in_(['no_sub', 'sub'])  # Только обычные пользователи
        )
    )

    result = await session.execute(stmt)
    return result.scalars().all()


async def send_inactivity_reminders(bot: Bot):
    """Отправляет напоминания каждую минуту"""
    async with AsyncSessionLocal() as session:
        try:
            users = await check_inactive_users(session)

            for user in users:
                try:
                    # Проверяем, что не отправляли напоминание совсем недавно
                    if user.last_interaction_time and (datetime.utcnow() - user.last_interaction_time) < timedelta(minutes=1):
                        continue

                    await bot.send_message(
                        chat_id=user.id,
                        text=await get_reminder_text(session, 'inactive')
                    )

                    # Обновляем время последнего напоминания
                    user.last_interaction_time = datetime.utcnow()
                    await session.commit()

                except Exception as e:
                    logger.error(f"Error sending to {user.id}: {e}")
                    await session.rollback()

        except Exception as e:
            logger.error(f"Reminder system error: {e}")


async def check_and_send_reminders(bot: Bot):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                users = await get_users_for_reminders(session)

                for user_id, username, status, last_active in users:
                    reminder_type = get_reminder_type(last_active)
                    text = await get_reminder_text(session, reminder_type)

                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text=text
                        )
                        logger.info(f"Sent to {username}")
                    except Exception as e:
                        logger.error(f"Send failed: {e}")

        except Exception as e:
            logger.error(f"Database error: {e}")
            raise


async def send_single_reminder(bot: Bot, session: AsyncSession, user_id: int, username: str, text: str):
    """Отправка одного напоминания с обработкой ошибок"""
    try:
        user = await session.get(User, user_id)
        user.last_reminder_time = datetime.utcnow()

        await bot.send_message(
            chat_id=user_id,
            text=text
        )
        logger.info(f"Sent reminder to {username}")

    except Exception as e:
        logger.error(f"Failed to send to {username}: {e}")


async def send_message_with_retry(bot: Bot, chat_id: int, text: str, retries=2):
    for attempt in range(retries):
        try:
            await bot.send_message(chat_id, text, request_timeout=10)
            return True
        except TelegramNetworkError:
            if attempt < retries - 1:
                await asyncio.sleep(2)
    return False


async def reminder_loop(bot: Bot):
    """Безопасный цикл напоминаний"""
    while True:
        try:
            logger.info("Starting reminder cycle...")
            await check_and_send_reminders(bot)
            logger.info("Reminder cycle completed")
        except Exception as e:
            logger.error(f"Reminder loop error: {e}")
        finally:
            await asyncio.sleep(60)  # Пауза 60 секунд


def get_reminder_type(last_active: datetime) -> str:
    """Определяет тип напоминания"""
    inactive_period = datetime.utcnow() - last_active
    return 'promo' if inactive_period < timedelta(hours=96) else 'inactive'
