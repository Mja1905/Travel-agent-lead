"""
SQLAlchemy модели базы данных
"""
from sqlalchemy import (
    Column, Integer, String, BigInteger, Boolean,
    DateTime, Text, JSON, ForeignKey, Date, Index
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Admin(Base):
    """Модель администратора"""
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100))
    full_name = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now())

    def __repr__(self):
        return f"<Admin {self.full_name} (@{self.username})>"


class Agent(Base):
    """Модель агента"""
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100))
    full_name = Column(String(200), nullable=False)
    position = Column(Integer, nullable=False, index=True)
    status = Column(String(20), default='active', index=True)  # active, paused, blocked
    leads_today = Column(Integer, default=0)
    leads_week = Column(Integer, default=0)
    leads_month = Column(Integer, default=0)
    leads_total = Column(Integer, default=0)
    last_lead_at = Column(DateTime)
    pause_reason = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now())

    # Relationships
    leads = relationship("Lead", back_populates="agent")
    daily_stats = relationship("DailyStat", back_populates="agent", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_agents_active', 'status'),
        Index('idx_agents_position', 'position'),
    )

    def __repr__(self):
        return f"<Agent {self.full_name} (#{self.position})>"


class Lead(Base):
    """Модель лида (комментария)"""
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id', ondelete='SET NULL'), index=True)
    client_telegram_id = Column(BigInteger)
    client_username = Column(String(100))
    client_full_name = Column(String(200))
    comment_text = Column(Text, nullable=False)
    comment_id = Column(BigInteger)
    post_id = Column(BigInteger)
    comment_link = Column(Text)
    distributed_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), index=True)
    response_time = Column(Integer)  # В секундах
    is_processed = Column(Boolean, default=False, index=True)

    # Relationships
    agent = relationship("Agent", back_populates="leads")

    __table_args__ = (
        Index('idx_leads_agent_id', 'agent_id'),
        Index('idx_leads_distributed_at', 'distributed_at'),
        Index('idx_leads_is_processed', 'is_processed'),
    )

    def __repr__(self):
        return f"<Lead #{self.id} for Agent #{self.agent_id}>"


class Setting(Base):
    """Модель настроек системы"""
    __tablename__ = 'settings'

    key = Column(String(100), primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now())

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"


class ActivityLog(Base):
    """Модель логов активности"""
    __tablename__ = 'activity_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    action = Column(String(100), nullable=False, index=True)
    details = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_activity_user_id', 'user_id'),
        Index('idx_activity_action', 'action'),
        Index('idx_activity_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ActivityLog {self.action} by {self.user_id}>"


class DailyStat(Base):
    """Модель ежедневной статистики"""
    __tablename__ = 'daily_stats'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    leads_count = Column(Integer, default=0)
    avg_response_time = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="daily_stats")

    __table_args__ = (
        Index('idx_daily_stats_date', 'date'),
        Index('idx_daily_stats_agent_date', 'agent_id', 'date', unique=True),
    )

    def __repr__(self):
        return f"<DailyStat Agent #{self.agent_id} on {self.date}>"
