import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

load_dotenv()

# Проверка переменных окружения
required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Путь к SSL-сертификату
SSL_CA_PATH = '/root/.cloud-certs/root.crt'

# Асинхронное подключение (рабочая версия)
async_engine = create_async_engine(
    f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}",
    connect_args={
        'ssl': {
            'ca': SSL_CA_PATH,
            'check_hostname': True
        }
    },
    echo=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    future=True
)

Base = declarative_base()
