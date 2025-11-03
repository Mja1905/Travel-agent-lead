"""
Подключение к базе данных
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging

from app.config import settings
from app.database.models import Base

logger = logging.getLogger(__name__)


# Создание engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # Для Railway
    echo=settings.LOG_LEVEL == "DEBUG",
    future=True
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """Инициализация базы данных"""
    try:
        logger.info("Инициализация базы данных...")
        Base.metadata.create_all(bind=engine)
        logger.info("База данных успешно инициализирована")
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")
        return False


@contextmanager
def get_db() -> Session:
    """Получить сессию БД (context manager)"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка БД: {e}")
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Получить сессию БД (для dependency injection)"""
    return SessionLocal()


async def check_db_connection() -> bool:
    """Проверка подключения к БД"""
    try:
        with get_db() as db:
            db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return False
