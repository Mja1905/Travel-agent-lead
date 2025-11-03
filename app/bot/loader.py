"""
Инициализация бота
"""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Создание бота
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Создание диспетчера
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def on_startup():
    """Действия при запуске бота"""
    logger.info("Бот запускается...")

    # Инициализация базы данных
    from app.database.connection import init_db
    if init_db():
        logger.info("База данных инициализирована")
    else:
        logger.error("Ошибка инициализации базы данных")

    # Регистрация хендлеров
    from app.handlers import admin, agent, channel
    dp.include_router(admin.router)
    dp.include_router(agent.router)
    dp.include_router(channel.router)

    logger.info("Хендлеры зарегистрированы")

    # Настройка планировщика для сброса статистики
    from app.bot.scheduler import setup_scheduler
    setup_scheduler()

    logger.info("Планировщик задач запущен")

    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"Бот запущен: @{bot_info.username}")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Бот останавливается...")
    await bot.session.close()
    logger.info("Бот остановлен")
