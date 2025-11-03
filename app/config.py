"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Настройки приложения"""

    # Bot settings
    BOT_TOKEN: str
    BOT_MODE: str = "polling"  # webhook or polling
    WEBHOOK_URL: Optional[str] = None
    PORT: int = 8000

    # Telegram settings
    CHANNEL_ID: int
    ADMIN_ID: int

    # Database
    DATABASE_URL: str

    # Redis (optional)
    REDIS_URL: Optional[str] = None

    # Application settings
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "Asia/Tashkent"
    MAX_AGENTS: int = 20
    DISTRIBUTION_DELAY: int = 1

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# Глобальный экземпляр настроек
settings = Settings()


# Валидация настроек
def validate_settings():
    """Проверка обязательных настроек"""
    required_fields = ['BOT_TOKEN', 'CHANNEL_ID', 'ADMIN_ID', 'DATABASE_URL']

    for field in required_fields:
        value = getattr(settings, field, None)
        if not value:
            raise ValueError(f"Missing required setting: {field}")

    if settings.BOT_MODE == "webhook" and not settings.WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL is required when BOT_MODE is webhook")

    return True
