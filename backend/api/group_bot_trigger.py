#!/usr/bin/env python3
"""
🤖 DEPRECATED: Старый групповой триггер - заменен на smart_bot_trigger.py
Используйте новый SmartBotTrigger для работы с системой умной памяти
"""

import logging
from typing import Optional

logger = logging.getLogger("chatumba.group_bot_trigger_deprecated")

# DEPRECATED: Используйте SmartBotTrigger из smart_bot_trigger.py

async def process_bot_trigger(chat_id: str, message_text: str, user_id: str) -> Optional[str]:
    """
    DEPRECATED: Перенаправляет на новый SmartBotTrigger
    """
    logger.warning("⚠️ Используется устаревший group_bot_trigger. Переключаемся на SmartBotTrigger")
    
    try:
        from .smart_bot_trigger import process_smart_bot_trigger
        return await process_smart_bot_trigger(chat_id, message_text, user_id)
    except Exception as e:
        logger.error(f"❌ Ошибка перенаправления на SmartBotTrigger: {e}")
        return "🤖 Привет! Что нового в группе?"
 