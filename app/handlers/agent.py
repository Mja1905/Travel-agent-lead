"""
Обработчики команд агентов
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from sqlalchemy.orm import Session
import logging

from app.database.models import Agent, Lead
from app.database.connection import get_db_session
from app.services.statistics import StatsService
from app.templates.messages import Messages

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start_agent(message: Message):
    """Приветствие для агента"""
    db = get_db_session()
    try:
        # Проверяем, зарегистрирован ли агент
        agent = db.query(Agent).filter_by(telegram_id=message.from_user.id).first()

        if not agent:
            # Проверяем по username
            if message.from_user.username:
                agent = db.query(Agent).filter_by(username=message.from_user.username).first()

                if agent:
                    # Обновляем telegram_id
                    agent.telegram_id = message.from_user.id
                    db.commit()
                    logger.info(f"Обновлен telegram_id для агента @{agent.username}")

        if not agent:
            await message.answer(
                "❌ Вы не зарегистрированы в системе.\n\n"
                "Обратитесь к администратору для добавления в систему."
            )
            return

        stats = await StatsService(db).get_agent_stats(agent.id)

        text = Messages.AGENT_START.format(
            full_name=agent.full_name,
            position=agent.position,
            status=Messages.format_status(agent.status),
            leads_today=stats['today'],
            leads_week=stats['week'],
            leads_total=stats['total']
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 Моя статистика", callback_data="agent:stats"),
                InlineKeyboardButton(text="❓ Помощь", callback_data="agent:help")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка в cmd_start_agent: {e}")
        await message.answer(Messages.ERROR)
    finally:
        db.close()


@router.message(Command("my_stats"))
async def cmd_my_stats(message: Message):
    """Личная статистика агента"""
    db = get_db_session()
    try:
        agent = db.query(Agent).filter_by(telegram_id=message.from_user.id).first()

        if not agent:
            await message.answer("❌ Вы не зарегистрированы в системе.")
            return

        stats = await StatsService(db).get_detailed_agent_stats(agent.id)

        text = Messages.AGENT_STATS.format(**stats)

        await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка в cmd_my_stats: {e}")
        await message.answer(Messages.ERROR)
    finally:
        db.close()


@router.message(Command("help"))
async def cmd_help_agent(message: Message):
    """Помощь для агента"""
    await message.answer(Messages.HELP_AGENT)


# Callback handlers
@router.callback_query(F.data.startswith("agent:"))
async def handle_agent_callbacks(callback: CallbackQuery):
    """Обработка callback кнопок агента"""
    db = get_db_session()
    try:
        action = callback.data.split(":")[1]

        if action == "stats":
            agent = db.query(Agent).filter_by(telegram_id=callback.from_user.id).first()
            if agent:
                stats = await StatsService(db).get_detailed_agent_stats(agent.id)
                text = Messages.AGENT_STATS.format(**stats)
                await callback.message.answer(text)

        elif action == "help":
            await callback.message.answer(Messages.HELP_AGENT)

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в handle_agent_callbacks: {e}")
        await callback.answer("Ошибка")
    finally:
        db.close()


@router.callback_query(F.data.startswith("lead:"))
async def handle_lead_callbacks(callback: CallbackQuery):
    """Обработка действий с лидами"""
    db = get_db_session()
    try:
        parts = callback.data.split(":")
        action = parts[1]
        lead_id = int(parts[2])

        lead = db.query(Lead).filter_by(id=lead_id).first()
        if not lead:
            await callback.answer("❌ Лид не найден", show_alert=True)
            return

        agent = db.query(Agent).filter_by(telegram_id=callback.from_user.id).first()
        if not agent or lead.agent_id != agent.id:
            await callback.answer("❌ Этот лид назначен не вам", show_alert=True)
            return

        if action == "taken":
            # Агент взял лид в работу
            lead.is_processed = True
            db.commit()

            await callback.answer(Messages.LEAD_TAKEN, show_alert=True)
            logger.info(f"Лид #{lead_id} взят в работу агентом {agent.full_name}")

        elif action == "reject":
            # Агент отказался от лида
            # TODO: Передать лид следующему агенту
            lead.is_processed = True
            db.commit()

            await callback.answer(Messages.LEAD_REJECTED, show_alert=True)
            logger.info(f"Агент {agent.full_name} отказался от лида #{lead_id}")

    except Exception as e:
        logger.error(f"Ошибка в handle_lead_callbacks: {e}")
        await callback.answer("Ошибка", show_alert=True)
    finally:
        db.close()
