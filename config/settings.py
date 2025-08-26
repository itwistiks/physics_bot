import os
import ssl
from os import getenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
DB_URL = f"mysql+aiomysql://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_HOST')}/{getenv('DB_NAME')}"

# Для отправки сообщений в поддержку
ADMIN_USER_ID = int(getenv('ADMIN_USER_ID'))
LEADS_TOKEN = getenv('LEADS_TOKEN')


# Настройки напоминаний
REMINDER_INTERVAL_MINUTES = 4320  # Интервал проверки
# Минимальный интервал между напоминаниями одному пользователю (в минутах)
MIN_REMINDER_GAP = 30
