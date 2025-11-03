"""
Шаблоны сообщений для бота
"""


class Messages:
    """Класс с шаблонами сообщений"""

    # Общие
    ERROR = "❌ Произошла ошибка. Попробуйте позже."
    ACCESS_DENIED = "❌ У вас нет доступа к этой команде."
    INVALID_FORMAT = "❌ Неверный формат команды."

    # Админ
    ADMIN_START = """
👑 <b>Панель администратора</b>

📊 <b>Текущая статистика:</b>
├ Текущая очередь: Агент №{current_position}
├ Лидов сегодня: {leads_today}
├ Лидов за неделю: {leads_week}
└ Всего лидов: {leads_total}

👥 <b>Агенты:</b>
├ Активных: {active_agents}
├ На паузе: {paused_agents}
└ Всего: {total_agents}

Выберите действие:
"""

    AGENT_ADDED = """
✅ <b>Агент добавлен!</b>

👤 Имя: {full_name}
💬 Username: @{username}
🔢 Позиция: №{position}
📅 Telegram ID: {telegram_id}

Агент может начать получать лидов.
"""

    AGENT_REMOVED = """
✅ <b>Агент удален</b>

👤 {full_name} (@{username})
🔢 Позиция: №{position}

Очередь автоматически пересчитана.
"""

    AGENT_PAUSED = """
⏸ <b>Агент поставлен на паузу</b>

👤 {full_name} (@{username})
💬 Причина: {reason}

Агент не будет получать новых лидов.
"""

    AGENT_RESUMED = """
▶️ <b>Агент возобновил работу</b>

👤 {full_name} (@{username})
🔢 Позиция: №{position}

Агент снова в очереди.
"""

    AGENTS_LIST = """
👥 <b>Список агентов</b>

{agents_list}

Всего агентов: {total}
"""

    STATS_DETAIL = """
📊 <b>Детальная статистика</b>

📈 <b>Общее:</b>
├ Всего лидов: {total_leads}
├ Сегодня: {today_leads}
├ Вчера: {yesterday_leads}
├ Эта неделя: {week_leads}
└ Этот месяц: {month_leads}

👥 <b>По агентам:</b>
{agents_stats}

🏆 <b>Топ-3 агента месяца:</b>
{top_agents}
"""

    # Агент
    AGENT_START = """
👋 Добро пожаловать, <b>{full_name}</b>!

📊 <b>Ваша статистика:</b>
├ Ваш номер: Агент №{position}
├ Статус: {status}
├ Лидов сегодня: {leads_today}
├ Лидов за неделю: {leads_week}
└ Всего лидов: {leads_total}

💡 <i>Бот автоматически отправит вам уведомление, когда придет ваша очередь получить лида.</i>
"""

    AGENT_STATS = """
📈 <b>Ваша детальная статистика</b>

📊 <b>Лиды:</b>
├ Сегодня: {today}
├ Вчера: {yesterday}
├ Эта неделя: {this_week}
├ Прошлая неделя: {last_week}
├ Этот месяц: {this_month}
├ Прошлый месяц: {last_month}
└ Всего: {total}

⏱ <b>Эффективность:</b>
├ Среднее время ответа: {avg_response_time}
└ Обработано лидов: {processed_percent}%

📊 <b>Ваша позиция:</b> №{position}
"""

    # Уведомления
    NEW_LEAD = """
🔥 <b>НОВЫЙ ЛИД!</b>

Ваша очередь: №{position}
{'─' * 30}
👤 <b>Клиент:</b> {client_name}
💬 <b>Username:</b> @{client_username}
📝 <b>Комментарий:</b> {comment_text}
📅 <b>Время:</b> {time}
{'─' * 30}

⏰ <i>Напишите клиенту как можно скорее!</i>

📊 Ваша статистика: {leads_today} лидов сегодня | {leads_total} всего
"""

    LEAD_REMINDER = """
⏰ <b>НАПОМИНАНИЕ!</b>

Прошло 10 минут с момента получения лида.
Не забудьте связаться с клиентом!

👤 Клиент: @{client_username}
📝 Комментарий: {comment_text}
"""

    LEAD_TAKEN = "✅ Лид взят в работу"
    LEAD_REJECTED = "❌ Вы отказались от лида. Он будет передан следующему агенту."

    AGENT_BLOCKED_NOTIFICATION = """
⚠️ <b>Агент заблокировал бота</b>

👤 {full_name} (@{username})
🔢 Позиция: №{position}

Статус агента изменен на "blocked".
"""

    # Помощь
    HELP_ADMIN = """
📖 <b>Команды администратора</b>

👥 <b>Управление агентами:</b>
/add_agent @username "Имя" - добавить агента
/remove_agent @username - удалить агента
/pause_agent @username "причина" - поставить на паузу
/resume_agent @username - возобновить работу
/agents - список всех агентов

📊 <b>Статистика:</b>
/stats - общая статистика
/agent_stats @username - статистика агента
/history [N] - история последних N распределений

⚙️ <b>Управление:</b>
/current - текущая очередь
/reset_queue - сброс очереди
/broadcast "текст" - рассылка агентам

💡 <i>Используйте кнопки в главном меню для быстрого доступа.</i>
"""

    HELP_AGENT = """
📖 <b>Помощь для агентов</b>

📊 <b>Команды:</b>
/start - главное меню
/my_stats - моя статистика
/help - эта справка

💡 <b>Как это работает:</b>

1️⃣ Бот отслеживает комментарии в канале
2️⃣ Распределяет их по очереди между агентами
3️⃣ Отправляет уведомление с информацией о клиенте
4️⃣ Вы связываетесь с клиентом

⚡️ <b>Важно:</b>
• Отвечайте клиентам быстро
• Нажмите "Взял в работу" после получения лида
• Если не можете взять лид - нажмите "Отказаться"

❓ Вопросы? Обратитесь к администратору.
"""

    @staticmethod
    def format_agent_line(agent, index: int) -> str:
        """Форматирование строки агента"""
        status_emoji = {
            'active': '✅',
            'paused': '⏸',
            'blocked': '🚫'
        }.get(agent.status, '❓')

        return (
            f"{status_emoji} <b>#{agent.position}</b> {agent.full_name} (@{agent.username})\n"
            f"   └ Лидов: {agent.leads_total} | Сегодня: {agent.leads_today}"
        )

    @staticmethod
    def format_status(status: str) -> str:
        """Форматирование статуса агента"""
        status_map = {
            'active': 'Активен ✅',
            'paused': 'На паузе ⏸',
            'blocked': 'Заблокирован 🚫'
        }
        return status_map.get(status, status)
