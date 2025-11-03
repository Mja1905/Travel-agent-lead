"""
Декораторы для проверки прав доступа
"""
from functools import wraps
from aiogram.types import Message, CallbackQuery
from sqlalchemy.orm import Session
import logging

from app.database.models import Admin, Agent
from app.database.connection import get_db_session

logger = logging.getLogger(__name__)


def admin_only(handler):
    """Декоратор для проверки прав админа"""
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        # Получаем telegram_id
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return

        # Проверяем в БД
        db = get_db_session()
        try:
            admin = db.query(Admin).filter_by(
                telegram_id=user_id,
                is_active=True
            ).first()

            if not admin:
                if isinstance(event, Message):
                    await event.answer("❌ У вас нет прав администратора")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ У вас нет прав администратора", show_alert=True)
                return

            # Добавляем db_session в kwargs
            kwargs['db_session'] = db
            return await handler(event, *args, **kwargs)
        finally:
            db.close()

    return wrapper


def agent_only(handler):
    """Декоратор для проверки регистрации агента"""
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        # Получаем telegram_id
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return

        # Проверяем в БД
        db = get_db_session()
        try:
            agent = db.query(Agent).filter_by(telegram_id=user_id).first()

            if not agent:
                if isinstance(event, Message):
                    await event.answer("❌ Вы не зарегистрированы в системе. Обратитесь к администратору.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ Вы не зарегистрированы", show_alert=True)
                return

            # Добавляем agent и db_session в kwargs
            kwargs['agent'] = agent
            kwargs['db_session'] = db
            return await handler(event, *args, **kwargs)
        finally:
            db.close()

    return wrapper


def log_action(action_name: str):
    """Декоратор для логирования действий"""
    def decorator(handler):
        @wraps(handler)
        async def wrapper(event, *args, **kwargs):
            user_id = None
            if isinstance(event, (Message, CallbackQuery)):
                user_id = event.from_user.id

            logger.info(f"Action: {action_name} by user {user_id}")

            result = await handler(event, *args, **kwargs)

            logger.info(f"Action completed: {action_name}")
            return result

        return wrapper
    return decorator
