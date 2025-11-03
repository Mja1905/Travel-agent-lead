"""
Обработчик комментариев в канале
"""
from aiogram import Router, F
from aiogram.types import Message
import logging

from app.config import settings
from app.database.connection import get_db_session
from app.services.distribution import LeadDistributor
from app.services.notifications import NotificationService
from app.utils.validators import is_lead_comment
from app.bot.loader import bot

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.chat.id == settings.CHANNEL_ID)
async def handle_channel_message(message: Message):
    """
    Обработка сообщений в канале
    Отслеживаем комментарии к постам
    """
    try:
        # Проверяем, что это комментарий к посту
        if not message.reply_to_message:
            logger.debug("Сообщение не является комментарием")
            return

        # Проверяем, что есть текст
        if not message.text:
            logger.debug("Комментарий без текста")
            return

        # Проверяем, является ли это лидом
        if not is_lead_comment(message.text):
            logger.info(f"Комментарий не является лидом: {message.text[:50]}...")
            return

        logger.info(f"Обнаружен лид-комментарий от @{message.from_user.username}")

        # Подготавливаем данные комментария
        comment_data = {
            'user_id': message.from_user.id,
            'username': message.from_user.username or 'нет',
            'full_name': message.from_user.full_name or 'Без имени',
            'text': message.text,
            'comment_id': message.message_id,
            'post_id': message.reply_to_message.message_id,
            'link': get_comment_link(message)
        }

        # Распределяем лид
        db = get_db_session()
        try:
            distributor = LeadDistributor(db)
            lead = await distributor.distribute_lead(comment_data)

            if lead:
                logger.info(f"Лид #{lead.id} успешно распределен")

                # Отправляем уведомление агенту
                notifier = NotificationService(bot, db)
                notification_sent = await notifier.notify_agent(lead)

                if notification_sent:
                    logger.info(f"Уведомление отправлено агенту для лида #{lead.id}")
                else:
                    logger.error(f"Не удалось отправить уведомление для лида #{lead.id}")

                # Опционально: уведомляем админа
                # await notifier.notify_admin(lead)

            else:
                logger.error("Не удалось распределить лид")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Ошибка при обработке комментария: {e}")


def get_comment_link(message: Message) -> str:
    """
    Получить ссылку на комментарий

    Args:
        message: Объект сообщения

    Returns:
        str: Ссылка на комментарий
    """
    try:
        # Если канал имеет username
        if message.chat.username:
            return (
                f"https://t.me/{message.chat.username}/"
                f"{message.reply_to_message.message_id}?comment={message.message_id}"
            )
        else:
            # Если канал приватный, используем ID
            chat_id = str(message.chat.id).replace("-100", "")
            return (
                f"https://t.me/c/{chat_id}/"
                f"{message.reply_to_message.message_id}?comment={message.message_id}"
            )
    except Exception as e:
        logger.error(f"Ошибка при формировании ссылки: {e}")
        return ""


@router.channel_post(F.chat.id == settings.CHANNEL_ID)
async def handle_channel_post(message: Message):
    """
    Обработка постов в канале (не комментариев)
    Эта функция нужна для обработки именно постов, если понадобится
    """
    logger.debug(f"Обнаружен пост в канале: {message.message_id}")
    # Пока ничего не делаем с постами, только с комментариями
