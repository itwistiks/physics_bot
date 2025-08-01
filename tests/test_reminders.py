import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.services.reminder_service import send_inactivity_reminders
from sqlalchemy.ext.asyncio import AsyncSession
import warnings
from sqlalchemy import exc as sa_exc

# Подавляем предупреждения SQLAlchemy
warnings.filterwarnings("ignore", category=sa_exc.SAWarning)


@pytest.mark.asyncio
async def test_reminder_logic():
    # Тестовые данные
    test_users = [
        MagicMock(id=123, username="test_user",
                  status="no_sub", last_interaction_time=None),
        MagicMock(id=456, username="premium_user",
                  status="sub", last_interaction_time=None)
    ]

    # Моки
    mock_bot = AsyncMock()
    mock_session = MagicMock(spec=AsyncSession)

    # Мокируем зависимости
    with (
        patch('core.services.reminder_service.check_inactive_users',
              new=AsyncMock(return_value=test_users)),
        patch('core.services.reminder_service.get_reminder_text',
              new=AsyncMock(return_value="Test reminder")),
        patch('core.services.reminder_service.AsyncSessionLocal',
              return_value=mock_session)
    ):
        # Вызываем тестируемую функцию
        await send_inactivity_reminders(mock_bot)

    # Проверки
    assert mock_bot.send_message.call_count == 2
    mock_bot.send_message.assert_any_call(chat_id=123, text="Test reminder")
    mock_bot.send_message.assert_any_call(chat_id=456, text="Test reminder")
