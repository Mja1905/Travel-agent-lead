"""
Настройка логирования
"""
import logging
import sys
from app.config import settings


def setup_logger():
    """Настройка логгера"""
    # Создаем логгер
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_handler.setFormatter(formatter)

    # Добавляем handler
    logger.addHandler(console_handler)

    # Отключаем лишние логи от библиотек
    logging.getLogger('aiogram').setLevel(logging.INFO)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

    return logger


def setup_sentry():
    """Настройка Sentry мониторинга"""
    if not settings.SENTRY_DSN:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
            ],
            traces_sample_rate=0.1,
            environment="production",
            release="lead-bot@1.0.0"
        )

        logging.info("Sentry мониторинг активирован")
    except Exception as e:
        logging.error(f"Ошибка при инициализации Sentry: {e}")
