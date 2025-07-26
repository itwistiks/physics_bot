import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'auth_plugin': 'mysql_native_password'  # Важно для MySQL 8+
}

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute("SELECT @@version")
    print(f"✅ Успех! Версия MySQL: {cursor.fetchone()[0]}")
    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    print(f"❌ Ошибка {err.errno}: {err.msg}")
    print("Конфиг:", config)
except Exception as e:
    print(f"⚠ Неожиданная ошибка: {e}")
