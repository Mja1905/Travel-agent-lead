"""
Сервис уведомлений
"""
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.database.models import Lead, Agent, Admin
from app.templates.messages import Messages

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений"""

    def __init__(self, bot: Bot, db_session: Session):
        self.bot = bot
        self.db = db_session

    async def notify_agent(self, lead: Lead) -> bool:
        """
        Отправить уведомление агенту о новом лиде

        Args:
            lead: Объект лида

        Returns:
            bool: Успешность отправки
        """
        try:
            agent = self.db.query(Agent).filter_by(id=lead.agent_id).first()
            if not agent:
                logger.error(f"Агент не найден для лида #{lead.id}")
                return False

            # Формируем текст уведомления
            text = Messages.NEW_LEAD.format(
                position=agent.position,
                client_name=lead.client_full_name or 'Без имени',
                client_username=lead.client_username or 'нет',
                comment_text=lead.comment_text,
                time=lead.distributed_at.strftime('%d.%m.%Y %H:%M'),
                leads_today=agent.leads_today,
                leads_total=agent.leads_total
            )

            # Кнопки
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Перейти к комментарию",
                        url=lead.comment_link
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Взял в работу",
                        callback_data=f"lead:taken:{lead.id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Отказаться",
                        callback_data=f"lead:reject:{lead.id}"
                    )
                ]
            ])

            # Отправляем уведомление
            await self.bot.send_message(
                chat_id=agent.telegram_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=False
            )

            logger.info(f"Уведомление отправлено агенту {agent.full_name} (лид #{lead.id})")
            return True

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления агенту: {e}")

            # Если агент заблокировал бота
            if "Forbidden: bot was blocked" in str(e) or "blocked by user" in str(e).lower():
                try:
                    agent = self.db.query(Agent).filter_by(id=lead.agent_id).first()
                    if agent:
                        agent.status = 'blocked'
                        self.db.commit()
                        await self.notify_admin_about_blocked_agent(agent)
                        logger.warning(f"Агент {agent.full_name} заблокировал бота")
                except Exception as inner_e:
                    logger.error(f"Ошибка при обновлении статуса агента: {inner_e}")

            return False

    async def notify_admin(self, lead: Lead, message: str = None) -> bool:
        """
        Уведомить админа

        Args:
            lead: Объект лида
            message: Опциональное сообщение

        Returns:
            bool: Успешность отправки
        """
        try:
            admin = self.db.query(Admin).filter_by(is_active=True).first()
            if not admin:
                return False

            agent = self.db.query(Agent).filter_by(id=lead.agent_id).first()

            if not message:
                message = f"""
✅ <b>Лид распределён</b>

Лид №{lead.id}
Агент: №{agent.position} ({agent.full_name})
Клиент: @{lead.client_username or 'нет username'}
Комментарий: "{lead.comment_text[:50]}..."
Время: {lead.distributed_at.strftime('%H:%M')}
"""

            await self.bot.send_message(
                chat_id=admin.telegram_id,
                text=message,
                parse_mode="HTML"
            )

            return True

        except Exception as e:
            logger.error(f"Ошибка при уведомлении админа: {e}")
            return False

    async def notify_admin_about_blocked_agent(self, agent: Agent) -> bool:
        """
        Уведомить админа о заблокированном агенте

        Args:
            agent: Объект агента

        Returns:
            bool: Успешность отправки
        """
        try:
            admin = self.db.query(Admin).filter_by(is_active=True).first()
            if not admin:
                return False

            text = Messages.AGENT_BLOCKED_NOTIFICATION.format(
                full_name=agent.full_name,
                username=agent.username,
                position=agent.position
            )

            await self.bot.send_message(
                chat_id=admin.telegram_id,
                text=text,
                parse_mode="HTML"
            )

            return True

        except Exception as e:
            logger.error(f"Ошибка при уведомлении админа о блокировке: {e}")
            return False

    async def send_reminder(self, lead_id: int) -> bool:
        """
        Отправить напоминание агенту о лиде

        Args:
            lead_id: ID лида

        Returns:
            bool: Успешность отправки
        """
        try:
            lead = self.db.query(Lead).filter_by(id=lead_id).first()
            if not lead or lead.is_processed:
                return False

            agent = self.db.query(Agent).filter_by(id=lead.agent_id).first()
            if not agent:
                return False

            text = Messages.LEAD_REMINDER.format(
                client_username=lead.client_username or 'нет',
                comment_text=lead.comment_text[:100]
            )

            # Кнопка для перехода
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Перейти к комментарию",
                        url=lead.comment_link
                    )
                ]
            ])

            await self.bot.send_message(
                chat_id=agent.telegram_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=False
            )

            logger.info(f"Напоминание отправлено агенту {agent.full_name} (лид #{lead.id})")
            return True

        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания: {e}")
            return False

    async def broadcast_to_agents(self, message: str, active_only: bool = True) -> tuple:
        """
        Рассылка сообщения всем агентам

        Args:
            message: Текст сообщения
            active_only: Только активным агентам

        Returns:
            tuple: (успешно, ошибок)
        """
        try:
            query = self.db.query(Agent)
            if active_only:
                query = query.filter_by(status='active')

            agents = query.all()

            success = 0
            errors = 0

            for agent in agents:
                try:
                    await self.bot.send_message(
                        chat_id=agent.telegram_id,
                        text=message,
                        parse_mode="HTML"
                    )
                    success += 1
                except Exception as e:
                    logger.error(f"Ошибка рассылки агенту {agent.full_name}: {e}")
                    errors += 1

            logger.info(f"Рассылка завершена: {success} успешно, {errors} ошибок")
            return (success, errors)

        except Exception as e:
            logger.error(f"Ошибка при рассылке: {e}")
            return (0, 0)
