"""
Сервис распределения лидов (Round Robin)
"""
from typing import Optional
from datetime import datetime
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.database.models import Agent, Lead, Setting

logger = logging.getLogger(__name__)


class LeadDistributor:
    """Класс для распределения лидов между агентами"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.lock = asyncio.Lock()

    async def get_next_agent(self) -> Optional[Agent]:
        """
        Получить следующего агента в очереди (Round Robin)
        """
        async with self.lock:
            try:
                # Получаем текущую позицию из настроек
                current_position_setting = self.db.query(Setting).filter_by(
                    key='current_position'
                ).first()

                if not current_position_setting:
                    current_position_setting = Setting(key='current_position', value='1')
                    self.db.add(current_position_setting)
                    self.db.commit()

                current_position = int(current_position_setting.value)

                # Получаем всех активных агентов отсортированных по позиции
                active_agents = self.db.query(Agent).filter_by(
                    status='active'
                ).order_by(Agent.position).all()

                if not active_agents:
                    logger.error("Нет активных агентов для распределения")
                    return None

                # Находим следующего агента
                next_agent = None
                for agent in active_agents:
                    if agent.position >= current_position:
                        next_agent = agent
                        break

                # Если не нашли (дошли до конца), берем первого
                if not next_agent:
                    next_agent = active_agents[0]

                # Обновляем позицию для следующего раза
                next_position = next_agent.position + 1
                max_position = max(a.position for a in active_agents)

                if next_position > max_position:
                    next_position = active_agents[0].position

                current_position_setting.value = str(next_position)

                # Обновляем статистику агента
                next_agent.leads_today += 1
                next_agent.leads_week += 1
                next_agent.leads_month += 1
                next_agent.leads_total += 1
                next_agent.last_lead_at = datetime.utcnow()

                self.db.commit()

                logger.info(f"Следующий агент: {next_agent.full_name} (позиция {next_agent.position})")
                return next_agent

            except Exception as e:
                logger.error(f"Ошибка при получении следующего агента: {e}")
                self.db.rollback()
                return None

    async def distribute_lead(self, comment_data: dict) -> Optional[Lead]:
        """
        Распределить лид агенту

        Args:
            comment_data: Данные комментария
                {
                    'user_id': int,
                    'username': str,
                    'full_name': str,
                    'text': str,
                    'comment_id': int,
                    'post_id': int,
                    'link': str
                }

        Returns:
            Lead: Созданный лид или None
        """
        try:
            # Получаем следующего агента
            agent = await self.get_next_agent()
            if not agent:
                logger.error("Не удалось получить агента для распределения")
                return None

            # Создаем запись о лиде
            lead = Lead(
                agent_id=agent.id,
                client_telegram_id=comment_data.get('user_id'),
                client_username=comment_data.get('username'),
                client_full_name=comment_data.get('full_name'),
                comment_text=comment_data.get('text'),
                comment_id=comment_data.get('comment_id'),
                post_id=comment_data.get('post_id'),
                comment_link=comment_data.get('link')
            )

            self.db.add(lead)

            # Обновляем общую статистику
            total_leads_setting = self.db.query(Setting).filter_by(
                key='total_leads'
            ).first()

            if not total_leads_setting:
                total_leads_setting = Setting(key='total_leads', value='1')
                self.db.add(total_leads_setting)
            else:
                total_leads_setting.value = str(int(total_leads_setting.value) + 1)

            self.db.commit()

            logger.info(f"Лид #{lead.id} распределен агенту {agent.full_name} (#{agent.position})")
            return lead

        except Exception as e:
            logger.error(f"Ошибка при распределении лида: {e}")
            self.db.rollback()
            return None

    async def get_current_position(self) -> int:
        """Получить текущую позицию в очереди"""
        try:
            setting = self.db.query(Setting).filter_by(key='current_position').first()
            if setting:
                return int(setting.value)
            return 1
        except Exception as e:
            logger.error(f"Ошибка при получении текущей позиции: {e}")
            return 1

    async def reset_queue(self) -> bool:
        """Сбросить очередь в начало"""
        try:
            setting = self.db.query(Setting).filter_by(key='current_position').first()
            if setting:
                setting.value = '1'
            else:
                setting = Setting(key='current_position', value='1')
                self.db.add(setting)

            self.db.commit()
            logger.info("Очередь сброшена")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сбросе очереди: {e}")
            self.db.rollback()
            return False

    async def reorder_agents(self) -> bool:
        """Пересчитать позиции агентов после удаления"""
        try:
            agents = self.db.query(Agent).order_by(Agent.position).all()

            for index, agent in enumerate(agents, start=1):
                agent.position = index

            self.db.commit()
            logger.info("Позиции агентов пересчитаны")
            return True
        except Exception as e:
            logger.error(f"Ошибка при пересчете позиций: {e}")
            self.db.rollback()
            return False
