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

4. **Структура проекта**:

```
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

## 🗃 Актуальная труктура проекта

```
physics_bot/
├── config/                         # Конфигурационные файлы
│   ├── __pycache__/                # Кэш Python
│   ├── __init__.py                 # Инициализация пакета
│   ├── database.py                 # Настройки подключения к БД
│   └── settings.py                 # Основные настройки приложения
│
├── core/                           # Основной код приложения
│   ├── __pycache__/                # Кэш Python
│   ├── __init__.py                 # Инициализация пакета
│   │
│   ├── database/                   # Работа с базой данных
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   └── models.py               # Модели SQLAlchemy
│   │
│   ├── fsm/                        # Конечные автоматы (FSM)
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   └── states.py               # Состояния бота
│   │
│   ├── handlers/                   # Обработчики сообщений
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── db_test.py              # Тесты базы данных
│   │   ├── inline_handlers.py      # Обработчики инлайн-кнопок
│   │   ├── menu_handlers.py        # Обработчики меню
│   │   └── start.py                # Обработчики команд /start
│   │
│   ├── keyboards/                  # Клавиатуры бота
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── inline_menu.py          # Инлайн-меню (устаревшее)
│   │   ├── inline.py               # Инлайн-клавиатуры
│   │   ├── main_menu.py            # Главное меню
│   │   └── reply.py                # Reply-клавиатуры
│   │
│   ├── services/                   # Сервисные функции
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   └── task_service.py         # Сервис работы с заданиями
│   │
│   └── bot.py                      # Основной файл инициализации бота
│
├── migrations/                     # Миграции базы данных
│   ├── __pycache__/
│   ├── versions/                   # Файлы миграций
│   │   ├── __pycache__/
│   │   ├── 02dc0f20e0f7_initial_tables.py
│   │   ├── 4124def56530_fix_relationships_between_task_and_py
│   │   └── a740b916aae3_fix_relationships_between_task_and_py
│   │
│   ├── env.py                      # Конфиг Alembic
│   ├── README                      # Документация
│   └── script.py.mako              # Шаблон для создания миграций
│
├── physics_bot.egg-info/           # Метаданные пакета
├── tests/                          # Тесты
├── venv/                           # Виртуальное окружение
│
├── .env                            # Переменные окружения
├── .env.example                    # Шаблон .env файла
├── .gitignore                      # Игнорируемые файлы
├── alembic.ini                     # Конфигурация Alembic
├── README.md                       # Документация проекта
├── requirements.txt                # Зависимости
└── setup.py                        # Настройка пакета
```
