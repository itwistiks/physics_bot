import os
import ssl
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


load_dotenv()


Base = declarative_base()
engine = create_engine(os.getenv('DB_FULL_URL'))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DB_URL = f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"


# Создаем SSL контекст
# ssl_context = ssl.create_default_context(cafile='/root/.cloud-certs/root.crt')
# ssl_context.check_hostname = False
# ssl_context.verify_mode = ssl.CERT_REQUIRED


engine = create_async_engine(
    DB_URL,
    echo=True,  # Включеное логирование SQL-запросов
    pool_pre_ping=True,  # Проверка соединений перед использованием
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    # connect_args={
    #     "ssl": ssl_context  # ← ВОТ ЭТО ГЛАВНОЕ!
    # }
)  # echo=True для логов SQL

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    future=True
)

Base = declarative_base()
