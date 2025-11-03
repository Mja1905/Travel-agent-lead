"""
Обработчики команд администратора
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from sqlalchemy.orm import Session
import logging
import re

from app.utils.decorators import admin_only, log_action
from app.services.statistics import StatsService
from app.services.distribution import LeadDistributor
from app.services.notifications import NotificationService
from app.database.models import Agent
from app.templates.messages import Messages
from app.utils.validators import validate_telegram_username, extract_username
from app.bot.loader import bot

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
@admin_only
async def cmd_start_admin(message: Message, db_session: Session):
    """Главное меню админа"""
    try:
        stats = StatsService(db_session)
        current_stats = await stats.get_current_stats()

        text = Messages.ADMIN_START.format(**current_stats)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
                InlineKeyboardButton(text="👥 Агенты", callback_data="admin:agents")
            ],
            [
                InlineKeyboardButton(text="📜 История", callback_data="admin:history"),
                InlineKeyboardButton(text="⚙️ Текущая очередь", callback_data="admin:current")
            ],
            [
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast"),
                InlineKeyboardButton(text="❓ Помощь", callback_data="admin:help")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка в cmd_start_admin: {e}")
        await message.answer(Messages.ERROR)


@router.message(Command("stats"))
@admin_only
async def cmd_stats(message: Message, db_session: Session):
    """Детальная статистика по всем агентам"""
    try:
        stats = StatsService(db_session)
        agents_stats = await stats.get_agents_statistics()

        if not agents_stats:
            await message.answer("📊 Пока нет статистики")
            return

        text = "📊 <b>Статистика по агентам:</b>\n\n"

        for agent in agents_stats:
            status_emoji = "✅" if agent['status'] == 'active' else ("⏸" if agent['status'] == 'paused' else "🚫")
            text += f"{status_emoji} <b>{agent['name']}</b> (@{agent['username']})\n"
            text += f"├ Позиция: №{agent['position']}\n"
            text += f"├ Сегодня: {agent['leads_today']}\n"
            text += f"├ Неделя: {agent['leads_week']}\n"
            text += f"├ Месяц: {agent['leads_month']}\n"
            text += f"├ Всего: {agent['leads_total']}\n"
            text += f"└ Ср. время ответа: {agent['avg_response_time']}с\n\n"

        # Топ агенты
        text += "🏆 <b>Топ-3 агента месяца:</b>\n"
        top_agents = sorted(agents_stats, key=lambda x: x['leads_month'], reverse=True)[:3]

        medals = ["🥇", "🥈", "🥉"]
        for i, agent in enumerate(top_agents):
            medal = medals[i] if i < 3 else "👤"
            text += f"{medal} {agent['name']}: {agent['leads_month']} лидов\n"

        await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка в cmd_stats: {e}")
        await message.answer(Messages.ERROR)


@router.message(Command("add_agent"))
@admin_only
@log_action("add_agent")
async def cmd_add_agent(message: Message, db_session: Session):
    """
    Добавить нового агента
    Формат: /add_agent @username "Полное Имя"
    """
    try:
        # Парсинг команды
        match = re.match(r'/add_agent\s+@?(\w+)\s+"([^"]+)"', message.text)
        if not match:
            await message.answer(
                "❌ Неверный формат.\n\n"
                "Используйте: /add_agent @username \"Полное Имя\"\n\n"
                "Пример: /add_agent @john_doe \"Джон Доу\""
            )
            return

        username = match.group(1)
        full_name = match.group(2)

        # Проверка username
        if not validate_telegram_username(username):
            await message.answer("❌ Неверный формат username")
            return

        # Проверка на существование
        existing_agent = db_session.query(Agent).filter_by(username=username).first()
        if existing_agent:
            await message.answer(f"❌ Агент @{username} уже существует")
            return

        # Получаем максимальную позицию
        max_position = db_session.query(Agent).count()
        new_position = max_position + 1

        # Создаем агента (без telegram_id пока)
        agent = Agent(
            telegram_id=0,  # Будет обновлено когда агент напишет боту
            username=username,
            full_name=full_name,
            position=new_position,
            status='active'
        )

        db_session.add(agent)
        db_session.commit()

        text = Messages.AGENT_ADDED.format(
            full_name=full_name,
            username=username,
            position=new_position,
            telegram_id="Не установлен (агент должен написать /start боту)"
        )

        await message.answer(text)
        logger.info(f"Добавлен агент @{username} на позицию {new_position}")

    except Exception as e:
        logger.error(f"Ошибка в cmd_add_agent: {e}")
        await message.answer(Messages.ERROR)
        db_session.rollback()


@router.message(Command("remove_agent"))
@admin_only
@log_action("remove_agent")
async def cmd_remove_agent(message: Message, db_session: Session):
    """
    Удалить агента
    Формат: /remove_agent @username или /remove_agent 5
    """
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer("❌ Укажите username (@username) или позицию агента")
            return

        arg = args[1].strip()

        # Поиск агента
        agent = None
        if arg.startswith('@'):
            username = arg[1:]
            agent = db_session.query(Agent).filter_by(username=username).first()
        elif arg.isdigit():
            position = int(arg)
            agent = db_session.query(Agent).filter_by(position=position).first()

        if not agent:
            await message.answer(f"❌ Агент не найден: {arg}")
            return

        # Удаляем агента
        full_name = agent.full_name
        username = agent.username
        position = agent.position

        db_session.delete(agent)
        db_session.commit()

        # Пересчитываем позиции
        distributor = LeadDistributor(db_session)
        await distributor.reorder_agents()

        text = Messages.AGENT_REMOVED.format(
            full_name=full_name,
            username=username,
            position=position
        )

        await message.answer(text)
        logger.info(f"Удален агент @{username}")

    except Exception as e:
        logger.error(f"Ошибка в cmd_remove_agent: {e}")
        await message.answer(Messages.ERROR)
        db_session.rollback()


@router.message(Command("pause_agent"))
@admin_only
@log_action("pause_agent")
async def cmd_pause_agent(message: Message, db_session: Session):
    """
    Поставить агента на паузу
    Формат: /pause_agent @username "причина"
    """
    try:
        match = re.match(r'/pause_agent\s+@?(\w+)(?:\s+"([^"]+)")?', message.text)
        if not match:
            await message.answer(
                "❌ Неверный формат.\n\n"
                "Используйте: /pause_agent @username \"причина\"\n\n"
                "Пример: /pause_agent @john_doe \"Отпуск\""
            )
            return

        username = match.group(1)
        reason = match.group(2) or "Не указана"

        agent = db_session.query(Agent).filter_by(username=username).first()
        if not agent:
            await message.answer(f"❌ Агент @{username} не найден")
            return

        agent.status = 'paused'
        agent.pause_reason = reason
        db_session.commit()

        text = Messages.AGENT_PAUSED.format(
            full_name=agent.full_name,
            username=agent.username,
            reason=reason
        )

        await message.answer(text)
        logger.info(f"Агент @{username} поставлен на паузу")

    except Exception as e:
        logger.error(f"Ошибка в cmd_pause_agent: {e}")
        await message.answer(Messages.ERROR)
        db_session.rollback()


@router.message(Command("resume_agent"))
@admin_only
@log_action("resume_agent")
async def cmd_resume_agent(message: Message, db_session: Session):
    """
    Возобновить работу агента
    Формат: /resume_agent @username
    """
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer("❌ Укажите username агента")
            return

        username = args[1].strip().lstrip('@')

        agent = db_session.query(Agent).filter_by(username=username).first()
        if not agent:
            await message.answer(f"❌ Агент @{username} не найден")
            return

        agent.status = 'active'
        agent.pause_reason = None
        db_session.commit()

        text = Messages.AGENT_RESUMED.format(
            full_name=agent.full_name,
            username=agent.username,
            position=agent.position
        )

        await message.answer(text)
        logger.info(f"Агент @{username} возобновил работу")

    except Exception as e:
        logger.error(f"Ошибка в cmd_resume_agent: {e}")
        await message.answer(Messages.ERROR)
        db_session.rollback()


@router.message(Command("agents"))
@admin_only
async def cmd_agents(message: Message, db_session: Session):
    """Список всех агентов"""
    try:
        agents = db_session.query(Agent).order_by(Agent.position).all()

        if not agents:
            await message.answer("👥 Агентов пока нет")
            return

        text = "👥 <b>Список агентов</b>\n\n"

        for agent in agents:
            text += Messages.format_agent_line(agent, agent.position) + "\n\n"

        text += f"Всего агентов: {len(agents)}"

        await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка в cmd_agents: {e}")
        await message.answer(Messages.ERROR)


@router.message(Command("current"))
@admin_only
async def cmd_current(message: Message, db_session: Session):
    """Текущая позиция в очереди"""
    try:
        distributor = LeadDistributor(db_session)
        current_pos = await distributor.get_current_position()

        agent = db_session.query(Agent).filter_by(position=current_pos).first()

        if agent:
            text = f"📍 <b>Текущая очередь:</b> №{current_pos}\n\n"
            text += f"Следующий агент: {agent.full_name} (@{agent.username})"
        else:
            text = f"📍 <b>Текущая позиция:</b> №{current_pos}"

        await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка в cmd_current: {e}")
        await message.answer(Messages.ERROR)


@router.message(Command("history"))
@admin_only
async def cmd_history(message: Message, db_session: Session):
    """История распределений"""
    try:
        # Парсинг лимита
        args = message.text.split()
        limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 20

        stats = StatsService(db_session)
        history = await stats.get_lead_history(limit)

        if not history:
            await message.answer("📜 История пуста")
            return

        text = f"📜 <b>История распределений (последние {len(history)}):</b>\n\n"

        for lead in history:
            status = "✅" if lead['is_processed'] else "⏳"
            text += f"{status} Лид #{lead['id']}\n"
            text += f"├ Агент: {lead['agent_name']} (№{lead['agent_position']})\n"
            text += f"├ Клиент: @{lead['client_username']}\n"
            text += f"├ Текст: {lead['comment_text']}\n"
            text += f"└ Время: {lead['distributed_at']}\n\n"

        await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка в cmd_history: {e}")
        await message.answer(Messages.ERROR)


@router.message(Command("help"))
@admin_only
async def cmd_help_admin(message: Message, db_session: Session):
    """Помощь для админа"""
    await message.answer(Messages.HELP_ADMIN)


# Callback handlers
@router.callback_query(F.data.startswith("admin:"))
async def handle_admin_callbacks(callback: CallbackQuery, db_session: Session = None):
    """Обработка callback кнопок админа"""
    try:
        if not db_session:
            from app.database.connection import get_db_session
            db_session = get_db_session()

        action = callback.data.split(":")[1]

        if action == "stats":
            # Вызываем команду статистики
            await cmd_stats(callback.message, db_session)
        elif action == "agents":
            await cmd_agents(callback.message, db_session)
        elif action == "history":
            await cmd_history(callback.message, db_session)
        elif action == "current":
            await cmd_current(callback.message, db_session)
        elif action == "help":
            await cmd_help_admin(callback.message, db_session)

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в handle_admin_callbacks: {e}")
        await callback.answer("Ошибка")
