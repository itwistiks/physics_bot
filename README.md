# 📚 Physics Bot - Telegram Bot

![Python 3.11](https://www.python.org/downloads/windows/) Новые версии могут не работать
![Open Server Panel](https://img.shields.io/badge/MySQL-8.4-orange)
![phpMyAdmin](https://www.phpmyadmin.net/)

## 🚀 Первый день разработки: Базовый функционал

### ✅ Что реализовано:
1. **Создан новый бот в telegram**
   - Сообщение в @BotFather
   - Использование команды /newbot
     
2. **Ядро бота**:
   - Инициализация бота на aiogram 3.x
   - Настройка диспетчера и роутеров
   - Поддержка FSM (машины состояний)

3. **База данных**:
   - Подключение к MySQL через SQLAlchemy
   - Конфигурация через `.env`:
     ```ini
     DB_HOST=127.0.0.1
     DB_USER=bot_name
     DB_PASSWORD=password_bot
     DB_NAME=db_name
     ```

4. **Структура проекта**:
physics_bot/
├── core/
│ ├── init.py
│ ├── bot.py         # Инициализация бота
│ └── handlers/      # Обработчики команд
│     ├── init.py
│     └── start.py   # Команда /start
├── config/
│ ├── init.py 
│ └── settings.py    # Настройки подключения
├── .env.example     # Шаблон конфига
├── requirements.txt # Зависимости
└── README.md



### ⚙️ Установка:
1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-логин/physics_bot.git
cd physics_bot

2. Настройте окружение:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

3. Запустите тестовый скрипт:
python test_db.py  # Проверка подключения к MySQL
python test.py     # Проверка работы бота
