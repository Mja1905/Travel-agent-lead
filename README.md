# 🤖 Telegram Lead Distribution Bot

Telegram-бот для автоматического распределения лидов (комментариев из канала) между турагентами по системе Round Robin.

## 📋 Описание

Бот отслеживает комментарии в Telegram-канале и автоматически распределяет их между турагентами по очереди, отправляя уведомления в личные сообщения. Это обеспечивает справедливое распределение клиентов.

## ✨ Основные функции

- 🔄 **Round Robin распределение** - справедливая очередь между агентами
- 🔔 **Автоматические уведомления** - агент получает сообщение с информацией о клиенте
- 📊 **Детальная статистика** - по каждому агенту и общая
- ⏸️ **Управление агентами** - добавление, удаление, пауза
- 📈 **Мониторинг** - логи, health checks, интеграция с Sentry
- 🚀 **Railway.app ready** - готов к деплою на Railway

## 🛠 Технологии

- **Python 3.11**
- **aiogram 3.x** - асинхронная библиотека для Telegram Bot API
- **PostgreSQL** - база данных
- **SQLAlchemy 2.0** - ORM
- **Redis** - кеширование (опционально)
- **Docker** - контейнеризация
- **Railway.app** - хостинг

## 🚀 Быстрый старт на Railway

### 1. Подготовка

1. Создайте бота в [@BotFather](https://t.me/botfather) и получите токен
2. Добавьте бота администратором в ваш канал
3. Получите ID канала (можно через [@userinfobot](https://t.me/userinfobot))
4. Получите ваш Telegram ID для админ-доступа

### 2. Деплой на Railway

1. Зайдите на [Railway.app](https://railway.app)
2. Нажмите **"New Project"** → **"Deploy from GitHub repo"**
3. Выберите этот репозиторий
4. Railway автоматически обнаружит Dockerfile

### 3. Добавление баз данных

#### PostgreSQL (обязательно):
1. В проекте нажмите **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway автоматически создаст переменную `DATABASE_URL`

#### Redis (опционально):
1. В проекте нажмите **"New"** → **"Database"** → **"Redis"**
2. Railway автоматически создаст переменную `REDIS_URL`

### 4. Настройка переменных окружения

В Railway Dashboard → Variables добавьте:

```bash
BOT_TOKEN=your_bot_token_from_botfather
CHANNEL_ID=-1001234567890
ADMIN_ID=123456789
BOT_MODE=webhook
WEBHOOK_URL=https://your-app.railway.app
```

Опциональные переменные:
```bash
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn
TIMEZONE=Asia/Tashkent
```

### 5. Запуск

Railway автоматически запустит деплой после добавления переменных. Проверьте логи в разделе **"Deployments"**.

## 💻 Локальная разработка

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/travel-agent-lead.git
cd travel-agent-lead

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка

Создайте файл `.env`:

```bash
cp .env.example .env
```

Заполните `.env` своими значениями:

```env
BOT_TOKEN=your_bot_token
BOT_MODE=polling
DATABASE_URL=postgresql://user:pass@localhost:5432/lead_bot
CHANNEL_ID=-1001234567890
ADMIN_ID=123456789
LOG_LEVEL=INFO
```

### Запуск

```bash
# В режиме polling (для разработки)
python app/main.py

# В режиме webhook (для продакшена)
BOT_MODE=webhook WEBHOOK_URL=https://your-domain.com python app/main.py
```

## 📚 Команды бота

### Для администратора:

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/stats` | Общая статистика |
| `/add_agent @username "Имя"` | Добавить агента |
| `/remove_agent @username` | Удалить агента |
| `/pause_agent @username "причина"` | Поставить на паузу |
| `/resume_agent @username` | Возобновить работу |
| `/agents` | Список всех агентов |
| `/current` | Текущая позиция в очереди |
| `/history [N]` | История распределений |
| `/help` | Справка |

### Для агентов:

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и статистика |
| `/my_stats` | Моя детальная статистика |
| `/help` | Справка |

## 🏗 Структура проекта

```
travel-agent-lead/
├── app/
│   ├── bot/                 # Инициализация бота
│   │   ├── loader.py        # Загрузчик бота
│   │   ├── scheduler.py     # Планировщик задач
│   │   └── webhook.py       # Webhook сервер
│   ├── database/            # База данных
│   │   ├── models.py        # SQLAlchemy модели
│   │   └── connection.py    # Подключение к БД
│   ├── handlers/            # Обработчики команд
│   │   ├── admin.py         # Админ команды
│   │   ├── agent.py         # Команды агентов
│   │   └── channel.py       # Обработка комментариев
│   ├── services/            # Бизнес-логика
│   │   ├── distribution.py  # Распределение лидов
│   │   ├── statistics.py    # Статистика
│   │   └── notifications.py # Уведомления
│   ├── utils/               # Утилиты
│   │   ├── logger.py
│   │   ├── decorators.py
│   │   └── validators.py
│   ├── templates/           # Шаблоны сообщений
│   │   └── messages.py
│   ├── config.py            # Конфигурация
│   └── main.py              # Точка входа
├── .github/workflows/       # CI/CD
├── requirements.txt         # Зависимости
├── Dockerfile              # Docker образ
├── railway.toml            # Railway конфигурация
└── README.md
```

## 🔧 Как это работает

1. **Мониторинг канала**: Бот отслеживает все комментарии в указанном канале
2. **Определение лидов**: Комментарии с ключевыми словами ("+", "хочу", "цена" и т.д.) определяются как лиды
3. **Round Robin**: Лид автоматически назначается следующему агенту в очереди
4. **Уведомление**: Агент получает сообщение с информацией о клиенте и ссылкой на комментарий
5. **Статистика**: Система записывает всю статистику распределений

## 📊 Мониторинг

- **Health check**: `https://your-app.railway.app/health`
- **Логи**: Railway Dashboard → Deployments → View Logs
- **Метрики**: Railway Dashboard → Metrics
- **Sentry**: Интеграция для отслеживания ошибок

## 🔒 Безопасность

- Проверка прав доступа через декораторы
- Валидация входных данных
- Защита от SQL-инъекций (SQLAlchemy ORM)
- Логирование всех действий

## 🐛 Решение проблем

### Бот не отвечает
1. Проверьте токен бота в переменных окружения
2. Убедитесь что бот запущен (проверьте логи)
3. Проверьте что бот добавлен администратором в канал

### Не приходят уведомления агентам
1. Убедитесь что агент написал `/start` боту
2. Проверьте статус агента (не должен быть на паузе или заблокирован)
3. Проверьте текущую позицию в очереди `/current`

### Не распределяются лиды
1. Проверьте что есть активные агенты
2. Проверьте CHANNEL_ID в настройках
3. Посмотрите логи на наличие ошибок

### База данных не подключается
1. Проверьте DATABASE_URL
2. Убедитесь что PostgreSQL сервис запущен в Railway
3. Проверьте логи подключения

## 🤝 Вклад в проект

Если вы хотите внести вклад:

1. Fork проекта
2. Создайте ветку для новой функции (`git checkout -b feature/AmazingFeature`)
3. Commit изменений (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 📧 Контакты

Если у вас есть вопросы или предложения:

- Telegram: @your_username
- Email: your.email@example.com
- GitHub Issues: [создать issue](https://github.com/yourusername/travel-agent-lead/issues)

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) - отличная библиотека для работы с Telegram Bot API
- [Railway.app](https://railway.app) - простой и удобный хостинг
- Сообщество разработчиков Telegram ботов

---

**Сделано с ❤️ для автоматизации работы турагентств**
