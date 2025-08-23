import os
import ssl
from os import getenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
DB_URL = f"mysql+asyncmy://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_HOST')}/{getenv('DB_NAME')}"

# Для отправки сообщений в поддержку
ADMIN_USER_ID = int(getenv('ADMIN_USER_ID'))
LEADS_TOKEN = getenv('LEADS_TOKEN')


# SSL контекст для подключения
# ssl_context = ssl.create_default_context(cafile='/root/.cloud-certs/root.crt')
# ssl_context.check_hostname = False
# ssl_context.verify_mode = ssl.CERT_REQUIRED


# Настройки напоминаний
REMINDER_INTERVAL_MINUTES = 4320  # Интервал проверки
# Минимальный интервал между напоминаниями одному пользователю (в минутах)
MIN_REMINDER_GAP = 30
