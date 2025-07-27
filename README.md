# 📚 Physics Bot - Telegram Bot

[![Python 3.11](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/downloads/windows/) _Новые версии могут не работать_

[![Open Server Panel](https://img.shields.io/badge/Open_Server-5.3.8-lightgrey)](https://ospanel.io/) _Версия с MySQL 8.4_

[![phpMyAdmin](https://img.shields.io/badge/phpMyAdmin-5.2.1-orange)](https://www.phpmyadmin.net/) _Для управления MySQL_

## 🚀 Первый день разработки: Базовый функционал

### ✅ Что реализовано:

1. **Создан новый бот в telegram**
   - Работа с @BotFather
   - Использование команды /newbot
   - Получен токен
2. **Ядро бота**:

   - Инициализация бота на aiogram 3.x
   - Настройка диспетчера и роутеров
   - Поддержка FSM (машины состояний)

3. **База данных**:

   - Подключение к MySQL через SQLAlchemy
   - Конфигурация через `.env.eaxmple`:
     ```ini
     DB_HOST=127.0.0.1
     DB_USER=bot_name
     DB_PASSWORD=password_bot
     DB_NAME=db_name
     ```

### 📅 День 2: Работа с задачами

**🆕 Новые возможности:**

1. **Модели данных:**

   - Созданы модели `Task`, `Theory`, `Topic`, `User`
   - Настроены связи между таблицами
   - Реализованы Alembic-миграции

2. **Функционал:**

   - Система поддержки с кулдауном
   - Обработчики для:
     - Случайных задач (`/random`)
     - Вывода задач с вариантами ответов

3. **Клавиатуры:**
   - Инлайн-кнопки для ответов
   - Навигация между заданиями

## ⚙️ Установка и запуск

### Требования:

- Python 3.11+
- MySQL 8.0+ или PostgreSQL
- Виртуальное окружение

1. Клонируйте репозиторий:

```bash
git clone https://github.com/itwistiks/physics_bot.git
cd physics_bot
python -m venv venv
```

2. Настройте окружение и установка зависимостей:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Настройте `.env`

```
BOT_TOKEN=6123456789:AAHjKLMNopQRsTuVWXyZ-1234567890_abcDE
DB_HOST=127.0.0.1
DB_USER=bot_name
DB_PASSWORD=password_bot
DB_NAME=db_name
DB_FULL_URL=mysql+mysqlconnector://${DB_USER}:${DB_PASSWORD}@${DB_HOST}/${DB_NAME}?charset=charset
ADMIN_USER_ID=USER_ID
LEADS_TOKEN=9999999999:AAHjKLMNopQRsTuVWXyZ-1234567890_abcDE
```

4. Примените миграции

```bash
alembic upgrade head
```

5. Запустите тестовый скрипт:

```bash
python test_db.py  # Проверка подключения к MySQL
python test.py     # Проверка работы бота
```

## 🗃 Актуальная структура проекта

```
physics_bot/
├── config/
│   ├── __init__.py         # Инициализация пакета
│   ├── database.py         # Настройки AsyncSessionLocal и подключения к БД
│   └── settings.py         # Конфигурационные параметры
│
├── core/
│   ├── database/
│   │   ├── __init__.py
│   │   └── models.py       # Модели SQLAlchemy (Task, Theory и др.)
│   │
│   ├── fsm/
│   │   ├── __init__.py
│   │   └── states.py       # Состояния бота (TaskStates и др.)
│   │
│   ├── handlers/
│   │   ├── __init__.py     # Роутеры handlers
│   │   ├── inline_handlers.py  # Обработчики inline-кнопок
│   │   ├── reply_handlers.py   # Обработчики reply-кнопок
│   │   └── start.py        # Обработчики команды /start
│   │
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── inline.py       # Все inline-клавиатуры
│   │   └── reply.py        # Все reply-клавиатуры
│   │
│   ├── services/
│   │   ├── __init__.py     # Экспорт сервисов
│   │   ├── task_display.py # Логика отображения заданий
│   │   ├── task_service.py # Основные сервисные функции
│   │   └── task_utils.py   # Утилиты для работы с БД
│   │
│   ├── __init__.py
│   └── bot.py              # Основной файл инициализации бота
│
├── migrations/             # Миграции базы данных
│
├── tests/
│   ├── __init__.py
│   ├── test_db_bot.py      # Тесты (не импортируются в bot.py)
│   ├── test_db.py
│   └── test.py             # Основной файл запуска бота. Нужно вынести в отдельное место и переименовать
│
├── .env                    # Переменные окружения
├── .gitignore              # Игнорируемые файлы
├── alembic.ini             # Конфигурация Alembic
├── README.md               # Документация проекта
├── requirements.txt        # Зависимости
└── setup.py                # Настройка пакета
```
