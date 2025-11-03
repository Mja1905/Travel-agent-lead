"""
Сервис статистики
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.database.models import Agent, Lead, Setting, DailyStat

logger = logging.getLogger(__name__)


class StatsService:
    """Сервис для работы со статистикой"""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def get_current_stats(self) -> Dict:
        """Получить текущую статистику системы"""
        try:
            # Текущая позиция
            current_position_setting = self.db.query(Setting).filter_by(
                key='current_position'
            ).first()
            current_position = int(current_position_setting.value) if current_position_setting else 1

            # Лиды
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)

            leads_today = self.db.query(Lead).filter(
                func.date(Lead.distributed_at) == today
            ).count()

            leads_week = self.db.query(Lead).filter(
                func.date(Lead.distributed_at) >= week_ago
            ).count()

            total_leads_setting = self.db.query(Setting).filter_by(
                key='total_leads'
            ).first()
            leads_total = int(total_leads_setting.value) if total_leads_setting else 0

            # Агенты
            active_agents = self.db.query(Agent).filter_by(status='active').count()
            paused_agents = self.db.query(Agent).filter_by(status='paused').count()
            total_agents = self.db.query(Agent).count()

            return {
                'current_position': current_position,
                'leads_today': leads_today,
                'leads_week': leads_week,
                'leads_total': leads_total,
                'active_agents': active_agents,
                'paused_agents': paused_agents,
                'total_agents': total_agents
            }

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {}

    async def get_agents_statistics(self) -> List[Dict]:
        """Получить статистику по всем агентам"""
        try:
            agents = self.db.query(Agent).order_by(Agent.position).all()

            result = []
            for agent in agents:
                # Среднее время ответа
                avg_response = self.db.query(
                    func.avg(Lead.response_time)
                ).filter(
                    Lead.agent_id == agent.id,
                    Lead.response_time.isnot(None)
                ).scalar()

                result.append({
                    'id': agent.id,
                    'telegram_id': agent.telegram_id,
                    'name': agent.full_name,
                    'username': agent.username,
                    'position': agent.position,
                    'status': agent.status,
                    'leads_today': agent.leads_today,
                    'leads_week': agent.leads_week,
                    'leads_month': agent.leads_month,
                    'leads_total': agent.leads_total,
                    'avg_response_time': int(avg_response) if avg_response else 0,
                    'last_lead_at': agent.last_lead_at
                })

            return result

        except Exception as e:
            logger.error(f"Ошибка при получении статистики агентов: {e}")
            return []

    async def get_agent_stats(self, agent_id: int) -> Dict:
        """Получить статистику конкретного агента"""
        try:
            agent = self.db.query(Agent).filter_by(id=agent_id).first()
            if not agent:
                return {}

            return {
                'today': agent.leads_today,
                'week': agent.leads_week,
                'month': agent.leads_month,
                'total': agent.leads_total,
                'position': agent.position,
                'status': agent.status
            }

        except Exception as e:
            logger.error(f"Ошибка при получении статистики агента: {e}")
            return {}

    async def get_detailed_agent_stats(self, agent_id: int) -> Dict:
        """Получить детальную статистику агента"""
        try:
            agent = self.db.query(Agent).filter_by(id=agent_id).first()
            if not agent:
                return {}

            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            week_start = today - timedelta(days=today.weekday())
            last_week_start = week_start - timedelta(days=7)
            month_start = today.replace(day=1)
            last_month_end = month_start - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)

            # Лиды по периодам
            leads_yesterday = self.db.query(Lead).filter(
                Lead.agent_id == agent_id,
                func.date(Lead.distributed_at) == yesterday
            ).count()

            leads_this_week = self.db.query(Lead).filter(
                Lead.agent_id == agent_id,
                func.date(Lead.distributed_at) >= week_start
            ).count()

            leads_last_week = self.db.query(Lead).filter(
                Lead.agent_id == agent_id,
                func.date(Lead.distributed_at) >= last_week_start,
                func.date(Lead.distributed_at) < week_start
            ).count()

            leads_this_month = self.db.query(Lead).filter(
                Lead.agent_id == agent_id,
                func.date(Lead.distributed_at) >= month_start
            ).count()

            leads_last_month = self.db.query(Lead).filter(
                Lead.agent_id == agent_id,
                func.date(Lead.distributed_at) >= last_month_start,
                func.date(Lead.distributed_at) < month_start
            ).count()

            # Среднее время ответа
            avg_response = self.db.query(
                func.avg(Lead.response_time)
            ).filter(
                Lead.agent_id == agent_id,
                Lead.response_time.isnot(None)
            ).scalar()

            # Процент обработанных лидов
            total_leads = self.db.query(Lead).filter_by(agent_id=agent_id).count()
            processed_leads = self.db.query(Lead).filter_by(
                agent_id=agent_id,
                is_processed=True
            ).count()

            processed_percent = int((processed_leads / total_leads * 100)) if total_leads > 0 else 0

            return {
                'today': agent.leads_today,
                'yesterday': leads_yesterday,
                'this_week': leads_this_week,
                'last_week': leads_last_week,
                'this_month': leads_this_month,
                'last_month': leads_last_month,
                'total': agent.leads_total,
                'avg_response_time': f"{int(avg_response)}с" if avg_response else "N/A",
                'processed_percent': processed_percent,
                'position': agent.position
            }

        except Exception as e:
            logger.error(f"Ошибка при получении детальной статистики: {e}")
            return {}

    async def get_lead_history(self, limit: int = 50) -> List[Dict]:
        """Получить историю распределения лидов"""
        try:
            leads = self.db.query(Lead).order_by(
                Lead.distributed_at.desc()
            ).limit(limit).all()

            result = []
            for lead in leads:
                agent = self.db.query(Agent).filter_by(id=lead.agent_id).first()

                result.append({
                    'id': lead.id,
                    'agent_name': agent.full_name if agent else "N/A",
                    'agent_position': agent.position if agent else 0,
                    'client_username': lead.client_username,
                    'comment_text': lead.comment_text[:50] + "..." if len(lead.comment_text) > 50 else lead.comment_text,
                    'distributed_at': lead.distributed_at.strftime('%d.%m.%Y %H:%M'),
                    'is_processed': lead.is_processed
                })

            return result

        except Exception as e:
            logger.error(f"Ошибка при получении истории: {e}")
            return []

    async def reset_daily_stats(self) -> bool:
        """Сброс ежедневной статистики (вызывается в полночь)"""
        try:
            agents = self.db.query(Agent).all()
            for agent in agents:
                agent.leads_today = 0

            self.db.commit()
            logger.info("Ежедневная статистика сброшена")
            return True

        except Exception as e:
            logger.error(f"Ошибка при сбросе статистики: {e}")
            self.db.rollback()
            return False
