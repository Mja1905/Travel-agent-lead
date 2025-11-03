"""
Валидаторы данных
"""
import re
from typing import Optional


def validate_telegram_username(username: str) -> bool:
    """Проверка валидности Telegram username"""
    if not username:
        return False

    # Убираем @ если есть
    username = username.lstrip('@')

    # Проверяем формат (5-32 символа, только буквы, цифры и _)
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    return bool(re.match(pattern, username))


def validate_telegram_id(telegram_id: int) -> bool:
    """Проверка валидности Telegram ID"""
    # Telegram ID обычно положительные числа
    return telegram_id > 0


def extract_username(text: str) -> Optional[str]:
    """Извлечение username из текста"""
    # Ищем @username
    match = re.search(r'@([a-zA-Z0-9_]{5,32})', text)
    if match:
        return match.group(1)
    return None


def is_lead_comment(text: str) -> bool:
    """Проверка, является ли комментарий лидом"""
    if not text or len(text.strip()) < 1:
        return False

    text_lower = text.lower()

    # Паттерны для определения лидов
    lead_patterns = [
        r'\+',
        r'хочу',
        r'интерес',
        r'подроб',
        r'цена',
        r'сколько',
        r'стоимость',
        r'забронир',
        r'заказ',
        r'узнать',
        r'информац',
        r'свяж',
        r'напиш',
        r'звон',
        r'whatapp',
        r'whatsapp',
        r'viber'
    ]

    # Проверяем паттерны
    for pattern in lead_patterns:
        if re.search(pattern, text_lower):
            return True

    return False


def format_phone_number(phone: str) -> str:
    """Форматирование номера телефона"""
    # Убираем все кроме цифр и +
    cleaned = re.sub(r'[^\d+]', '', phone)
    return cleaned


def sanitize_text(text: str, max_length: int = 500) -> str:
    """Очистка и обрезание текста"""
    if not text:
        return ""

    # Убираем лишние пробелы
    text = ' '.join(text.split())

    # Обрезаем если нужно
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text
