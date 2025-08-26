import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
from urllib.parse import quote_plus
import ssl

load_dotenv()

Base = declarative_base()

# Экранируем пароль
db_password = os.getenv('DB_PASSWORD')
escaped_password = quote_plus(db_password)

# URL для aiomysql (БЕЗ SSL параметров в URL!)
DB_URL = f"mysql+aiomysql://{os.getenv('DB_USER')}:{escaped_password}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # SSL контекст для aiomysql
# ssl_context = ssl.create_default_context(cafile='/root/.cloud-certs/root.crt')
# ssl_context.check_hostname = False

# # Параметры подключения для aiomysql
# connect_args = {
#     "ssl": ssl_context
# }

engine = create_async_engine(
    DB_URL,
    echo=True,
    # connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)
