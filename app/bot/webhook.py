"""
Webhook сервер
"""
from aiohttp import web
from aiogram import Dispatcher
import logging
from datetime import datetime

from app.database.connection import check_db_connection

logger = logging.getLogger(__name__)


async def health_check(request):
    """Health check endpoint для Railway"""
    try:
        # Проверяем подключение к БД
        db_status = await check_db_connection()

        if db_status:
            return web.json_response({
                'status': 'healthy',
                'database': 'connected',
                'bot': 'running',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return web.json_response({
                'status': 'unhealthy',
                'database': 'disconnected',
                'bot': 'running'
            }, status=503)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response({
            'status': 'error',
            'error': str(e)
        }, status=500)


async def handle_webhook(request, dispatcher: Dispatcher):
    """Обработка webhook запросов"""
    try:
        update_data = await request.json()
        from aiogram.types import Update
        update = Update(**update_data)
        await dispatcher.feed_update(dispatcher.bot, update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500)


def setup_webhook_app(dispatcher: Dispatcher, webhook_path: str = "/webhook") -> web.Application:
    """
    Настройка webhook приложения

    Args:
        dispatcher: Диспетчер aiogram
        webhook_path: Путь для webhook

    Returns:
        web.Application
    """
    app = web.Application()

    # Health check endpoint
    app.router.add_get('/health', health_check)

    # Webhook endpoint
    app.router.add_post(webhook_path, lambda req: handle_webhook(req, dispatcher))

    logger.info(f"Webhook сервер настроен на {webhook_path}")
    return app
