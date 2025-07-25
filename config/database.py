import os
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
engine = create_async_engine(DB_URL, echo=True)  # echo=True для логов SQL
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()
