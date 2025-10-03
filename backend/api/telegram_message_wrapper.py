"""
Обертка для интеграции улучшенной отправки сообщений с существующим кодом.
"""

import sys
import os
from typing import Optional

# Добавляем путь к backend для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .telegram_message_sender import send_long_telegram_message_improved, send_long_channel_message_improved
from config import TELEGRAM_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)


async def send_long_telegram_message(chat_id, text, parse_mode=None):
    """
    Обертка для улучшенной отправки длинных сообщений.
    Совместима с существующим кодом.
    """
    try:
        token = TELEGRAM_CONFIG.get("token")
        if not token:
            logger.error("❌ Токен бота не настроен в TELEGRAM_CONFIG")
            return False
        
        success = await send_long_telegram_message_improved(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            token=token
        )
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Ошибка в обертке send_long_telegram_message: {e}")
        return False


async def send_long_channel_message(text, parse_mode=None):
    """
    Обертка для улучшенной отправки длинных сообщений в канал.
    Совместима с существующим кодом.
    """
    try:
        token = TELEGRAM_CONFIG.get("token")
        channel_id = TELEGRAM_CONFIG.get("channel_id")
        
        if not token or not channel_id:
            logger.error("❌ Токен бота или ID канала не настроены в TELEGRAM_CONFIG")
            return False
        
        success = await send_long_channel_message_improved(
            text=text,
            parse_mode=parse_mode,
            channel_id=channel_id,
            token=token
        )
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Ошибка в обертке send_long_channel_message: {e}")
        return False 