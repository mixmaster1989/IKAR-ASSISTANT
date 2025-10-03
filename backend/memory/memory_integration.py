"""
🔗 Memory Integration - Интеграция новой системы памяти с существующими компонентами
Обеспечивает совместимость и плавный переход
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .smart_memory_manager import get_smart_memory_manager
from .night_optimizer import get_night_optimizer
from .smart_retriever import get_smart_retriever

logger = logging.getLogger("chatumba.memory_integration")

class MemoryIntegration:
    """Класс для интеграции новой системы памяти"""
    
    def __init__(self):
        self.memory_manager = None
        self.night_optimizer = None
        self.smart_retriever = None
        self.llm_client = None
        self.initialized = False
    
    async def initialize(self):
        """Инициализирует всю систему памяти"""
        try:
            logger.info("🚀 Инициализация новой системы памяти...")
            
            # Инициализируем LLM клиент
            from utils.component_manager import get_component_manager
            component_manager = get_component_manager()
            self.llm_client = component_manager.get_llm_client()
            
            # Инициализируем компоненты памяти
            self.memory_manager = get_smart_memory_manager()
            self.smart_retriever = get_smart_retriever(self.memory_manager)
            self.night_optimizer = get_night_optimizer(self.memory_manager, self.llm_client)
            
            # Запускаем ночную оптимизацию
            if self.night_optimizer:
                asyncio.create_task(self.night_optimizer.start_night_optimization())
                logger.info("🌙 Ночная оптимизация запущена")
            
            self.initialized = True
            logger.info("✅ Система памяти инициализирована успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации системы памяти: {e}")
            raise
    
    def add_group_message(self, chat_id: str, user_id: str, content: str, timestamp: float = None) -> bool:
        """Добавляет сообщение из группы в систему памяти"""
        if not self.initialized or not self.memory_manager:
            logger.warning("⚠️ Система памяти не инициализирована")
            return False
        
        return self.memory_manager.add_group_message(chat_id, user_id, content, timestamp)
    
    async def get_smart_context_for_bot(self, chat_id: str, query: str, user_id: str) -> Dict[str, Any]:
        """Получает умный контекст для бота"""
        if not self.initialized:
            logger.warning("⚠️ Система памяти не инициализирована")
            return {}
        
        try:
            # Получаем информацию о времени
            time_info = self.memory_manager.get_current_time_info()
            
            # Получаем свежую историю
            recent_messages = self.memory_manager.get_recent_messages(chat_id, limit=15)
            
            # Получаем релевантные чанки
            relevant_chunks = await self.smart_retriever.find_relevant_chunks(chat_id, query)
            
            # Получаем последние ответы бота
            recent_responses = self.memory_manager.get_recent_bot_responses(chat_id, limit=3)
            
            return {
                'time_info': time_info,
                'recent_messages': recent_messages,
                'relevant_chunks': relevant_chunks,
                'recent_responses': recent_responses,
                'memory_stats': await self.get_memory_stats(chat_id)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста: {e}")
            return {}
    
    def save_bot_response(self, chat_id: str, response: str, context_hash: str = None) -> bool:
        """Сохраняет ответ бота"""
        if not self.initialized or not self.memory_manager:
            return False
        
        return self.memory_manager.add_bot_response(chat_id, response, context_hash)
    
    async def force_optimize_chat(self, chat_id: str) -> Dict[str, Any]:
        """Принудительная оптимизация чата"""
        if not self.initialized or not self.night_optimizer:
            return {'status': 'error', 'message': 'Система не инициализирована'}
        
        return await self.night_optimizer.force_optimize_chat(chat_id)
    
    async def get_memory_stats(self, chat_id: str = None) -> Dict[str, Any]:
        """Получает статистику системы памяти"""
        if not self.initialized:
            return {}
        
        try:
            # Общая статистика
            general_stats = self.memory_manager.get_stats()
            
            # Статистика поисковика для конкретного чата
            retriever_stats = {}
            if chat_id and self.smart_retriever:
                retriever_stats = await self.smart_retriever.get_retriever_stats(chat_id)
            
            return {
                'general': general_stats,
                'retriever': retriever_stats,
                'optimizer_running': self.night_optimizer.is_running if self.night_optimizer else False
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def stop_optimization(self):
        """Останавливает ночную оптимизацию"""
        if self.night_optimizer:
            self.night_optimizer.stop_night_optimization()
            logger.info("🛑 Ночная оптимизация остановлена")

# Глобальный экземпляр интеграции
_memory_integration = None

def get_memory_integration() -> MemoryIntegration:
    """Получает глобальный экземпляр интеграции памяти"""
    global _memory_integration
    if _memory_integration is None:
        _memory_integration = MemoryIntegration()
    return _memory_integration

async def initialize_smart_memory_system():
    """Инициализирует всю систему умной памяти"""
    integration = get_memory_integration()
    await integration.initialize()
    return integration

# Функции для обратной совместимости с существующим кодом
def add_group_message_to_memory(chat_id: str, user_id: str, content: str, timestamp: float = None) -> bool:
    """Добавляет сообщение в память (функция совместимости)"""
    integration = get_memory_integration()
    return integration.add_group_message(chat_id, user_id, content, timestamp)

async def get_smart_memory_context(chat_id: str, query: str, user_id: str) -> Dict[str, Any]:
    """Получает контекст из умной памяти (функция совместимости)"""
    integration = get_memory_integration()
    return await integration.get_smart_context_for_bot(chat_id, query, user_id)