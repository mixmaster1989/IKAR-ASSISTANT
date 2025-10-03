"""
Модуль для управления личностями пользователей в Telegram.
"""
from typing import Dict
from core.personality import ChatumbaPersonality
from utils.logger import get_logger

logger = get_logger("chatumba.personality")

# Глобальное хранилище экземпляров личностей
personality_instances: Dict[str, ChatumbaPersonality] = {}

def get_personality(user_id: str) -> ChatumbaPersonality:
    """Получает или создает экземпляр личности для пользователя."""
    logger.debug(f"🔍 Запрос личности для: {user_id}")
    if user_id not in personality_instances:
        logger.info(f"🆕 Создание новой личности для: {user_id}")
        personality_instances[user_id] = ChatumbaPersonality(user_id)
        logger.info(f"✅ Личность создана для: {user_id}")
    else:
        logger.debug(f"🔄 Возвращаем существующую личность: {user_id}")
    return personality_instances[user_id]

def clear_personality(user_id: str) -> bool:
    """Удаляет личность пользователя."""
    if user_id in personality_instances:
        del personality_instances[user_id]
        logger.info(f"Удалена личность пользователя: {user_id}")
        return True
    return False

def get_active_personalities_count() -> int:
    """Возвращает количество активных личностей."""
    return len(personality_instances)