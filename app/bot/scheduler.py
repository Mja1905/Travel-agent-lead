"""
Планировщик задач
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import pytz

from app.config import settings
from app.database.connection import get_db_session
from app.services.statistics import StatsService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def reset_daily_stats():
    """Сброс ежедневной статистики в полночь"""
    logger.info("Выполняется сброс ежедневной статистики...")
    db = get_db_session()
    try:
        stats_service = StatsService(db)
        await stats_service.reset_daily_stats()
        logger.info("Ежедневная статистика сброшена успешно")
    except Exception as e:
        logger.error(f"Ошибка при сбросе статистики: {e}")
    finally:
        db.close()


def setup_scheduler():
    """Настройка планировщика"""
    try:
        timezone = pytz.timezone(settings.TIMEZONE)

        # Сброс ежедневной статистики в полночь
        scheduler.add_job(
            reset_daily_stats,
            CronTrigger(hour=0, minute=0, timezone=timezone),
            id='reset_daily_stats',
            name='Сброс ежедневной статистики',
            replace_existing=True
        )

        scheduler.start()
        logger.info("Планировщик задач запущен")

    except Exception as e:
        logger.error(f"Ошибка при настройке планировщика: {e}")
