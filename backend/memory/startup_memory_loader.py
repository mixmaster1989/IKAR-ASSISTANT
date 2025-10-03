"""
🚀 Startup Memory Loader - Загрузка всех сообщений из групп при запуске
Парсит все существующие сообщения и сразу создает чанки для тестирования системы
"""

import logging
import sqlite3
import asyncio
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger("chatumba.startup_loader")

class StartupMemoryLoader:
    """Загрузчик памяти при запуске системы"""
    
    def __init__(self):
        self.old_db_path = "data/chatumba.db"  # Старая база с группами
        self.processed_messages = 0
        self.created_chunks = 0
        self.processed_chats = []
    
    async def load_all_group_messages(self):
        """Загружает все сообщения из групп при запуске"""
        try:
            logger.info("🚀 Запуск загрузки всех групповых сообщений...")
            
            # Получаем все группы из старой базы
            group_chats = self._get_all_group_chats()
            
            if not group_chats:
                logger.info("📭 Нет групповых чатов для загрузки")
                return
            
            logger.info(f"📊 Найдено {len(group_chats)} групповых чатов")
            
            # Инициализируем компоненты памяти
            from memory.smart_memory_manager import get_smart_memory_manager
            from memory.night_optimizer import get_night_optimizer
            from utils.component_manager import get_component_manager
            
            memory_manager = get_smart_memory_manager()
            component_manager = get_component_manager()
            llm_client = component_manager.get_llm_client()
            night_optimizer = get_night_optimizer(memory_manager, llm_client)
            
            # Обрабатываем каждый чат
            for chat_id in group_chats:
                await self._process_chat_messages(chat_id, memory_manager, night_optimizer)
            
            logger.info(f"✅ Загрузка завершена: {self.processed_messages} сообщений, {self.created_chunks} чанков")
            logger.info(f"📋 Обработанные чаты: {self.processed_chats}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки групповых сообщений: {e}")
    
    def _get_all_group_chats(self) -> List[str]:
        """Получает список всех групповых чатов из старой базы"""
        try:
            if not Path(self.old_db_path).exists():
                logger.warning(f"⚠️ Старая база данных не найдена: {self.old_db_path}")
                return []
            
            conn = sqlite3.connect(self.old_db_path)
            cursor = conn.cursor()
            
            # Получаем уникальные chat_id из group_history
            cursor.execute("""
                SELECT DISTINCT chat_id 
                FROM group_history 
                WHERE chat_id IS NOT NULL 
                AND chat_id != ''
                ORDER BY chat_id
            """)
            
            chat_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            logger.info(f"🔍 Найдены группы: {chat_ids}")
            return chat_ids
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка чатов: {e}")
            return []
    
    async def _process_chat_messages(self, chat_id: str, memory_manager, night_optimizer):
        """Обрабатывает сообщения одного чата"""
        try:
            logger.info(f"📝 Обрабатываем чат {chat_id}...")
            
            # Получаем все сообщения чата из старой базы
            messages = self._get_chat_messages(chat_id)
            
            if not messages:
                logger.info(f"📭 Нет сообщений в чате {chat_id}")
                return
            
            logger.info(f"📊 Найдено {len(messages)} сообщений в чате {chat_id}")
            
            # Добавляем сообщения в новую систему памяти
            added_count = 0
            for msg in messages:
                success = memory_manager.add_group_message(
                    chat_id=msg['chat_id'],
                    user_id=msg['user_id'],
                    content=msg['content'],
                    timestamp=msg['timestamp']
                )
                if success:
                    added_count += 1
            
            logger.info(f"💾 Добавлено {added_count} сообщений в новую систему памяти")
            self.processed_messages += added_count
            
            # Проверяем, есть ли уже чанки для этого чата
            existing_chunks = self._check_existing_chunks(chat_id)
            
            if existing_chunks > 0:
                logger.info(f"✅ Чат {chat_id} уже имеет {existing_chunks} чанков - пропускаем чанкование")
            elif added_count > 0:
                logger.info(f"🔄 Запускаем принудительное чанкование для {chat_id}...")
                result = await night_optimizer.force_optimize_chat(chat_id)
                
                if result['status'] == 'success':
                    self.created_chunks += 1
                    logger.info(f"✅ Создан чанк для чата {chat_id}: {result.get('message', '')}")
                else:
                    logger.info(f"ℹ️ Чанкование для {chat_id}: {result.get('message', 'нет данных')}")
            else:
                logger.info(f"ℹ️ Нет новых сообщений для чанкования в {chat_id}")
            
            self.processed_chats.append(chat_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки чата {chat_id}: {e}")
    
    def _get_chat_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """Получает все сообщения чата из старой базы"""
        try:
            conn = sqlite3.connect(self.old_db_path)
            cursor = conn.cursor()
            
            # Получаем все сообщения чата, отсортированные по времени (БЕЗ ДУБЛИКАТОВ)
            cursor.execute("""
                SELECT DISTINCT chat_id, user_id, content, timestamp, type
                FROM group_history 
                WHERE chat_id = ? 
                AND content IS NOT NULL 
                AND content != ''
                AND content != '[photo]'
                AND content != '[voice]'
                AND type IN ('text', 'voice')
                ORDER BY timestamp ASC
            """, (chat_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'chat_id': row[0],
                    'user_id': row[1] or 'unknown',
                    'content': row[2],
                    'timestamp': row[3],
                    'type': row[4] or 'text'
                })
            
            conn.close()
            return messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщений чата {chat_id}: {e}")
            return []
    
    def _check_existing_chunks(self, chat_id: str) -> int:
        """Проверяет количество существующих чанков для чата"""
        try:
            from memory.smart_memory_manager import get_smart_memory_manager
            memory_manager = get_smart_memory_manager()
            
            conn = sqlite3.connect(memory_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM memory_chunks 
                WHERE chat_id = ?
            """, (chat_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки существующих чанков: {e}")
            return 0
    
    async def get_loading_stats(self) -> Dict[str, Any]:
        """Возвращает статистику загрузки"""
        return {
            'processed_messages': self.processed_messages,
            'created_chunks': self.created_chunks,
            'processed_chats': self.processed_chats,
            'total_chats': len(self.processed_chats)
        }

# Глобальный экземпляр загрузчика
_startup_loader = None

def get_startup_loader() -> StartupMemoryLoader:
    """Получает глобальный экземпляр загрузчика"""
    global _startup_loader
    if _startup_loader is None:
        _startup_loader = StartupMemoryLoader()
    return _startup_loader

async def initialize_memory_from_existing_groups():
    """Инициализирует память из существующих групп при запуске"""
    loader = get_startup_loader()
    await loader.load_all_group_messages()
    return loader