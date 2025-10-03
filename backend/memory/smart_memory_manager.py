"""
🧠 Smart Memory Manager - Центральная система умной памяти IKAR
Объединяет сбор, сжатие, поиск и временное затухание релевантности
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

logger = logging.getLogger("chatumba.smart_memory")

@dataclass
class MemoryMessage:
    """Сообщение из группы"""
    id: int
    chat_id: str
    user_id: str
    content: str
    timestamp: float
    processed: bool = False

@dataclass
class MemoryChunk:
    """Сжатый чанк памяти"""
    id: str
    chat_id: str
    topic: str
    content: str
    created_at: float
    source_period_start: float
    source_period_end: float
    relevance_base: float
    message_count: int
    participants: List[str]

@dataclass
class BotResponse:
    """Ответ бота для защиты от повторов"""
    chat_id: str
    content: str
    timestamp: float
    context_hash: str

class SmartMemoryManager:
    """Центральный менеджер умной памяти"""
    
    def __init__(self, db_path: str = "data/smart_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Настройки временного затухания
        self.relevance_thresholds = {
            7: 0.3,      # 0-7 дней: легко достать
            30: 0.5,     # 7-30 дней: средне
            90: 0.7,     # 30-90 дней: сложно
            float('inf'): 0.9  # 90+ дней: почти невозможно
        }
        
        # Настройки ночной оптимизации
        self.night_start = 23  # 23:00
        self.night_end = 7     # 07:00
        self.optimization_running = False
        
        # Кэш для производительности
        self.chunk_cache = {}
        self.response_cache = {}
        
        self._init_database()
        logger.info("🧠 SmartMemoryManager инициализирован")
    
    def _init_database(self):
        """Инициализация базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица сообщений из групп
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица сжатых чанков памяти
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_chunks (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    source_period_start REAL NOT NULL,
                    source_period_end REAL NOT NULL,
                    relevance_base REAL DEFAULT 0.5,
                    message_count INTEGER DEFAULT 0,
                    participants TEXT,
                    metadata TEXT
                )
            """)
            
            # Таблица ответов бота (защита от повторов)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    context_hash TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для производительности
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_time ON group_messages(chat_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_processed ON group_messages(processed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_chat_time ON memory_chunks(chat_id, created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_chat_time ON bot_responses(chat_id, timestamp)")
            
            # Уникальный индекс для предотвращения дубликатов сообщений
            # Сначала удаляем дубликаты, если они есть
            cursor.execute("""
                DELETE FROM group_messages 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM group_messages 
                    GROUP BY chat_id, user_id, content, timestamp
                )
            """)
            
            # Создаем уникальный индекс
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_unique 
                ON group_messages(chat_id, user_id, content, timestamp)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("✅ База данных Smart Memory инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
    
    def add_group_message(self, chat_id: str, user_id: str, content: str, timestamp: float = None) -> bool:
        """Добавляет сообщение из группы с защитой от дубликатов"""
        try:
            if timestamp is None:
                timestamp = time.time()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Пытаемся добавить сообщение (уникальный индекс предотвратит дубликаты)
            try:
                cursor.execute("""
                    INSERT INTO group_messages (chat_id, user_id, content, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (chat_id, user_id, content, timestamp))
                
                conn.commit()
                conn.close()
                
                logger.debug(f"📝 Добавлено новое сообщение в группу {chat_id}: {content[:50]}...")
                return True
                
            except sqlite3.IntegrityError as e:
                # Сообщение уже существует
                conn.close()
                logger.debug(f"🔄 Сообщение уже существует в группе {chat_id}: {content[:50]}...")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления сообщения: {e}")
            return False
    
    def get_recent_messages(self, chat_id: str, limit: int = 15) -> List[MemoryMessage]:
        """Получает последние сообщения из группы с удалением дубликатов"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем сообщения с удалением дубликатов по content
            cursor.execute("""
                SELECT id, chat_id, user_id, content, timestamp, processed
                FROM group_messages
                WHERE chat_id = ?
                GROUP BY content  -- Удаляем дубликаты по содержанию
                ORDER BY timestamp DESC
                LIMIT ?
            """, (chat_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                messages.append(MemoryMessage(
                    id=row[0],
                    chat_id=row[1],
                    user_id=row[2],
                    content=row[3],
                    timestamp=row[4],
                    processed=bool(row[5])
                ))
            
            conn.close()
            return list(reversed(messages))  # Хронологический порядок
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщений: {e}")
            return []
    
    def get_current_time_info(self) -> Dict[str, Any]:
        """Получает информацию о текущем времени"""
        now = datetime.now()
        return {
            'timestamp': time.time(),
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'weekday': now.strftime('%A'),
            'hour': now.hour,
            'is_night': self._is_night_time(),
            'is_weekend': now.weekday() >= 5,
            'time_of_day': self._get_time_of_day(now.hour)
        }
    
    def _is_night_time(self) -> bool:
        """Проверяет, ночное ли время для оптимизации"""
        hour = datetime.now().hour
        logger.debug(f"🌙 Проверка ночного времени: {hour}:00, night_start={self.night_start}, night_end={self.night_end}")
        
        if self.night_start > self.night_end:  # Переход через полночь
            is_night = hour >= self.night_start or hour < self.night_end
        else:
            is_night = self.night_start <= hour < self.night_end
        
        logger.debug(f"🌙 Результат проверки ночного времени: {is_night}")
        return is_night
    
    def _get_time_of_day(self, hour: int) -> str:
        """Определяет время суток"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 23:
            return "evening"
        else:
            return "night"
    
    def calculate_relevance_threshold(self, chunk_age_days: float) -> float:
        """Вычисляет порог релевантности на основе возраста чанка"""
        for max_age, threshold in self.relevance_thresholds.items():
            if chunk_age_days <= max_age:
                return threshold
        return 0.9  # Самый высокий порог для очень старых чанков
    
    def add_bot_response(self, chat_id: str, content: str, context_hash: str = None) -> bool:
        """Сохраняет ответ бота для защиты от повторов"""
        try:
            if context_hash is None:
                context_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Добавляем новый ответ
            cursor.execute("""
                INSERT INTO bot_responses (chat_id, content, timestamp, context_hash)
                VALUES (?, ?, ?, ?)
            """, (chat_id, content, time.time(), context_hash))
            
            # Оставляем только последние 5 ответов для каждого чата
            cursor.execute("""
                DELETE FROM bot_responses
                WHERE chat_id = ? AND id NOT IN (
                    SELECT id FROM bot_responses
                    WHERE chat_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 5
                )
            """, (chat_id, chat_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"💾 Сохранен ответ бота для группы {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения ответа бота: {e}")
            return False
    
    def get_recent_bot_responses(self, chat_id: str, limit: int = 3) -> List[BotResponse]:
        """Получает последние ответы бота"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT chat_id, content, timestamp, context_hash
                FROM bot_responses
                WHERE chat_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (chat_id, limit))
            
            responses = []
            for row in cursor.fetchall():
                responses.append(BotResponse(
                    chat_id=row[0],
                    content=row[1],
                    timestamp=row[2],
                    context_hash=row[3]
                ))
            
            conn.close()
            return responses
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения ответов бота: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Получает статистику системы памяти"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Статистика сообщений
            cursor.execute("SELECT COUNT(*) FROM group_messages")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM group_messages WHERE processed = FALSE")
            unprocessed_messages = cursor.fetchone()[0]
            
            # Статистика чанков
            cursor.execute("SELECT COUNT(*) FROM memory_chunks")
            total_chunks = cursor.fetchone()[0]
            
            # Статистика ответов бота
            cursor.execute("SELECT COUNT(*) FROM bot_responses")
            total_responses = cursor.fetchone()[0]
            
            # Активные чаты
            cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM group_messages")
            active_chats = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_messages': total_messages,
                'unprocessed_messages': unprocessed_messages,
                'total_chunks': total_chunks,
                'total_responses': total_responses,
                'active_chats': active_chats,
                'optimization_running': self.optimization_running,
                'is_night_time': self._is_night_time(),
                'current_time': self.get_current_time_info()
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}

# Глобальный экземпляр менеджера памяти
_smart_memory_manager = None

def get_smart_memory_manager() -> SmartMemoryManager:
    """Получает глобальный экземпляр менеджера памяти"""
    global _smart_memory_manager
    if _smart_memory_manager is None:
        _smart_memory_manager = SmartMemoryManager()
    return _smart_memory_manager