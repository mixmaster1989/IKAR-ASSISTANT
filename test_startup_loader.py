"""
🧪 Тест загрузчика существующих сообщений при запуске
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
)

logger = logging.getLogger("test_startup_loader")

async def test_startup_loader():
    """Тестирует загрузчик существующих сообщений"""
    try:
        logger.info("🚀 Тестирование загрузчика существующих сообщений...")
        
        # Инициализируем систему памяти
        from memory.memory_integration import initialize_smart_memory_system
        await initialize_smart_memory_system()
        
        # Запускаем загрузчик
        from memory.startup_memory_loader import initialize_memory_from_existing_groups
        loader = await initialize_memory_from_existing_groups()
        
        # Получаем статистику
        stats = await loader.get_loading_stats()
        
        logger.info("📊 РЕЗУЛЬТАТЫ ЗАГРУЗКИ:")
        logger.info(f"   📝 Обработано сообщений: {stats['processed_messages']}")
        logger.info(f"   📦 Создано чанков: {stats['created_chunks']}")
        logger.info(f"   💬 Обработано чатов: {stats['total_chats']}")
        logger.info(f"   📋 ID чатов: {stats['processed_chats']}")
        
        # Проверяем что данные действительно загружены
        from memory.smart_memory_manager import get_smart_memory_manager
        memory_manager = get_smart_memory_manager()
        
        system_stats = memory_manager.get_stats()
        logger.info("📈 СТАТИСТИКА СИСТЕМЫ ПАМЯТИ:")
        logger.info(f"   📝 Всего сообщений: {system_stats.get('total_messages', 0)}")
        logger.info(f"   📦 Всего чанков: {system_stats.get('total_chunks', 0)}")
        logger.info(f"   💬 Активных чатов: {system_stats.get('active_chats', 0)}")
        
        if stats['processed_messages'] > 0:
            logger.info("✅ Загрузчик работает корректно!")
        else:
            logger.info("ℹ️ Нет данных для загрузки (это нормально если нет старых сообщений)")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования загрузчика: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_startup_loader())