"""
📱 Telegram Memory Integration - Интеграция Telegram с новой системой памяти
Обеспечивает автоматическое сохранение сообщений и интеграцию с умным триггером
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("chatumba.telegram_memory")

class TelegramMemoryIntegration:
    """Класс для интеграции Telegram с системой памяти"""
    
    def __init__(self):
        self.memory_integration = None
        self.initialized = False
    
    async def initialize(self):
        """Инициализирует интеграцию с памятью"""
        try:
            from memory.memory_integration import get_memory_integration
            self.memory_integration = get_memory_integration()
            
            if not self.memory_integration.initialized:
                await self.memory_integration.initialize()
            
            self.initialized = True
            logger.info("✅ Telegram интеграция с памятью инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Telegram интеграции: {e}")
            raise
    
    def save_group_message(self, chat_id: str, user_id: str, content: str, timestamp: float = None) -> bool:
        """Сохраняет сообщение из группы в систему памяти"""
        if not self.initialized or not self.memory_integration:
            logger.warning("⚠️ Интеграция не инициализирована")
            return False
        
        try:
            # Сохраняем в новую систему памяти
            success = self.memory_integration.add_group_message(chat_id, user_id, content, timestamp)
            
            if success:
                logger.debug(f"💾 Сообщение сохранено в память: {chat_id} | {content[:50]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сообщения в память: {e}")
            return False
    
    async def handle_smart_bot_trigger(self, chat_id: str, message_text: str, user_id: str, 
                                      is_quote: bool = False, quoted_message_id: int = None, 
                                      is_mention: bool = False) -> Optional[str]:
        """Обрабатывает умный триггер бота (обычный, через цитирование или @username)"""
        if not self.initialized:
            logger.warning("⚠️ Интеграция не инициализирована")
            return None
        
        try:
            from api.smart_bot_trigger import process_smart_bot_trigger
            
            # Сначала сохраняем сообщение
            self.save_group_message(chat_id, user_id, message_text)
            
            # Затем обрабатываем триггер
            response = await process_smart_bot_trigger(chat_id, message_text, user_id, is_quote, quoted_message_id, is_mention)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки умного триггера: {e}")
            return None
    
    async def get_memory_stats_for_chat(self, chat_id: str) -> Dict[str, Any]:
        """Получает статистику памяти для чата"""
        if not self.initialized or not self.memory_integration:
            return {}
        
        try:
            return await self.memory_integration.get_memory_stats(chat_id)
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики памяти: {e}")
            return {}

# Глобальный экземпляр интеграции
_telegram_memory_integration = None

def get_telegram_memory_integration() -> TelegramMemoryIntegration:
    """Получает глобальный экземпляр Telegram интеграции"""
    global _telegram_memory_integration
    if _telegram_memory_integration is None:
        _telegram_memory_integration = TelegramMemoryIntegration()
    return _telegram_memory_integration

async def initialize_telegram_memory_integration():
    """Инициализирует Telegram интеграцию с памятью"""
    integration = get_telegram_memory_integration()
    await integration.initialize()
    return integration

# Функции для использования в telegram_polling.py
async def save_telegram_message_to_memory(chat_id: str, user_id: str, content: str, timestamp: float = None) -> bool:
    """Сохраняет сообщение Telegram в память"""
    integration = get_telegram_memory_integration()
    return integration.save_group_message(chat_id, user_id, content, timestamp)

async def handle_telegram_bot_trigger(chat_id: str, message_text: str, user_id: str) -> Optional[str]:
    """Обрабатывает триггер бота в Telegram"""
    integration = get_telegram_memory_integration()
    return await integration.handle_smart_bot_trigger(chat_id, message_text, user_id)