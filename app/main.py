"""
Главный файл приложения
Точка входа для Telegram-бота распределения лидов
"""
import asyncio
import logging
import sys

from aiogram import Bot
from aiohttp import web

from app.config import settings, validate_settings
from app.utils.logger import setup_logger, setup_sentry
from app.bot.loader import bot, dp, on_startup, on_shutdown
from app.bot.webhook import setup_webhook_app

logger = None


async def main():
    """Главная функция запуска"""
    global logger

    # Настройка логирования
    logger = setup_logger()

    # Настройка Sentry
    setup_sentry()

    logger.info("=" * 50)
    logger.info("Запуск Telegram Lead Distribution Bot")
    logger.info("=" * 50)

    try:
        # Валидация настроек
        validate_settings()
        logger.info("Конфигурация проверена")

        # Инициализация бота
        await on_startup()

        # Режим работы
        if settings.BOT_MODE == "webhook":
            await start_webhook()
        else:
            await start_polling()

    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        sys.exit(1)


async def start_polling():
    """Запуск в режиме polling"""
    logger.info("Запуск в режиме polling...")

    try:
        # Удаляем webhook если был установлен
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook удален")

        # Запуск polling
        logger.info("Бот готов к работе!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка в polling: {e}")
    finally:
        await on_shutdown()


async def start_webhook():
    """Запуск в режиме webhook"""
    logger.info("Запуск в режиме webhook...")

    try:
        # Настройка webhook
        webhook_url = f"{settings.WEBHOOK_URL}/webhook"

        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        logger.info(f"Webhook установлен: {webhook_url}")

        # Создание web приложения
        app = setup_webhook_app(dp)

        # Запуск web сервера
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, '0.0.0.0', settings.PORT)
        await site.start()

        logger.info(f"Webhook сервер запущен на порту {settings.PORT}")
        logger.info("Бот готов к работе!")

        # Держим сервер запущенным
        while True:
            await asyncio.sleep(3600)

    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
