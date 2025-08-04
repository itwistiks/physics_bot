import asyncio
from aiogram import Bot
from core.services.reminder_service import ReminderService
import logging

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.service = ReminderService(bot)
        self.task = None

    async def start(self):
        """Запускает периодическую проверку"""
        if self.task is None:
            self.task = asyncio.create_task(self.run())

    async def stop(self):
        """Останавливает scheduler"""
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

    async def run(self):
        """Основной цикл"""
        try:
            while True:
                try:
                    results = await self.service.send_reminders()
                    logger.info(f"Reminders sent: {results}")
                except Exception as e:
                    logger.error(f"Reminder error: {e}")

                await asyncio.sleep(3600)  # Каждый час
        except asyncio.CancelledError:
            logger.info("Scheduler stopped")
