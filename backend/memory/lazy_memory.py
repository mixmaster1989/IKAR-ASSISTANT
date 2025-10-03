"""
LazyMemory - простая система памяти на основе SQLite
Заменяет сложный FAISS на простой и эффективный поиск
"""

import sqlite3
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LazyMemory:
    """
    Простая система памяти с ленивой загрузкой
    - Полная история в SQLite
    - Поиск по ключевым словам
    - Кэш на время сессии
    """
    
    def __init__(self, db_path: str = "data/chatumba.db"):
        self.db_path = db_path
        self.cache = {}  # кэш на время сессии
        self.cache_ttl = 3600  # 1 час TTL
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных с индексами"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Принудительно создаем таблицу
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        chat_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        message_type TEXT DEFAULT 'text'
                    )
                """)
                
                # Проверяем что таблица создана
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
                if not cursor.fetchone():
                    logger.error("❌ Таблица messages не создана!")
                    raise Exception("Таблица messages не создана")
                
                # Создаем индексы для быстрого поиска
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_user_content 
                    ON messages(user_id, content)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                    ON messages(timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_user_timestamp 
                    ON messages(user_id, timestamp)
                """)
                
                conn.commit()
                logger.info("✅ LazyMemory: База данных инициализирована успешно")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации LazyMemory: {e}")
            raise
    
    def add_message(self, user_id: str, chat_id: str, content: str, message_type: str = "text"):
        """Добавляет сообщение в память"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (user_id, chat_id, content, message_type)
                    VALUES (?, ?, ?, ?)
                """, (user_id, chat_id, content, message_type))
                conn.commit()
                
                # Очищаем кэш для этого пользователя
                self._clear_user_cache(user_id)
                
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения: {e}")
    
    def get_relevant_history(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получает релевантную историю по запросу
        Использует простой поиск по ключевым словам
        """
        # Логирование отладки памяти
        try:
            import sys
            sys.path.append('backend')
            from utils.memory_debug_logger import get_memory_debug_logger
        except ImportError:
            # Fallback - создаем заглушку
            class DummyLogger:
                def log_lazy_memory_start(self, *args): pass
                def log_lazy_memory_cache(self, *args): pass
                def log_lazy_memory_keywords(self, *args): pass
                def log_lazy_memory_results(self, *args): pass
                def log_error(self, *args): pass
            def get_memory_debug_logger():
                return DummyLogger()
        debug_logger = get_memory_debug_logger()
        debug_logger.log_lazy_memory_start(user_id, query)
        
        try:
            # Проверяем кэш
            cache_key = f"{user_id}:{query}"
            if cache_key in self.cache:
                cache_time, cache_data = self.cache[cache_key]
                if datetime.now().timestamp() - cache_time < self.cache_ttl:
                    debug_logger.log_lazy_memory_cache(True, cache_key)
                    logger.debug(f"LazyMemory: Используем кэш для {user_id}")
                    return cache_data
            
            debug_logger.log_lazy_memory_cache(False, cache_key)
            
            # Извлекаем ключевые слова
            keywords = self._extract_keywords(query)
            debug_logger.log_lazy_memory_keywords(keywords)
            
            if not keywords:
                # Если нет ключевых слов, берем последние сообщения
                results = self._get_recent_messages(user_id, limit)
                debug_logger.log_lazy_memory_results(len(results), results)
                return results
            
            # Ищем по ключевым словам
            results = self._search_by_keywords(user_id, keywords, limit)
            
            # Кэшируем результат
            self.cache[cache_key] = (datetime.now().timestamp(), results)
            
            debug_logger.log_lazy_memory_results(len(results), results)
            logger.debug(f"LazyMemory: Найдено {len(results)} релевантных сообщений для {user_id}")
            return results
            
        except Exception as e:
            debug_logger.log_error("lazy_memory", e, {"user_id": user_id, "query": query})
            logger.error(f"Ошибка поиска истории: {e}")
            return self._get_recent_messages(user_id, limit)
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Извлекает ключевые слова из запроса"""
        # Убираем стоп-слова и знаки препинания
        stop_words = {
            'что', 'как', 'где', 'когда', 'почему', 'зачем', 'кто', 'какой',
            'это', 'то', 'вот', 'там', 'здесь', 'сейчас', 'тогда', 'всегда',
            'никогда', 'иногда', 'часто', 'редко', 'очень', 'слишком',
            'и', 'или', 'но', 'а', 'да', 'нет', 'не', 'ни', 'же', 'ли',
            'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о'
        }
        
        # Очищаем запрос
        clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
        words = clean_query.split()
        
        # Фильтруем стоп-слова и короткие слова
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Возвращаем топ-3 ключевых слова
        return keywords[:3]
    
    def _search_by_keywords(self, user_id: str, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        """Поиск по ключевым словам"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Строим SQL запрос с LIKE для каждого ключевого слова
                conditions = []
                params = [user_id]
                
                for keyword in keywords:
                    conditions.append("content LIKE ?")
                    params.append(f"%{keyword}%")
                
                where_clause = " OR ".join(conditions)
                
                query = f"""
                    SELECT content, timestamp, message_type
                    FROM messages 
                    WHERE user_id = ? AND ({where_clause})
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                params.append(limit)
                
                cursor.execute(query, params)
                results = []
                
                for row in cursor.fetchall():
                    results.append({
                        'content': row[0],
                        'timestamp': row[1],
                        'message_type': row[2]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Ошибка поиска по ключевым словам: {e}")
            return []
    
    def _get_recent_messages(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Получает последние сообщения пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content, timestamp, message_type
                    FROM messages 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (user_id, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'content': row[0],
                        'timestamp': row[1],
                        'message_type': row[2]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Ошибка получения последних сообщений: {e}")
            return []
    
    def _clear_user_cache(self, user_id: str):
        """Очищает кэш для пользователя"""
        keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self.cache[key]
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Получает статистику памяти для пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общее количество сообщений
                cursor.execute("""
                    SELECT COUNT(*) FROM messages WHERE user_id = ?
                """, (user_id,))
                total_messages = cursor.fetchone()[0]
                
                # Сообщения за последние 24 часа
                cursor.execute("""
                    SELECT COUNT(*) FROM messages 
                    WHERE user_id = ? AND timestamp > datetime('now', '-1 day')
                """, (user_id,))
                recent_messages = cursor.fetchone()[0]
                
                # Размер кэша
                cache_size = len(self.cache)
                
                return {
                    'total_messages': total_messages,
                    'recent_messages': recent_messages,
                    'cache_size': cache_size,
                    'cache_ttl': self.cache_ttl
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def clear_old_messages(self, days: int = 30):
        """Очищает старые сообщения"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM messages 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"LazyMemory: Удалено {deleted_count} старых сообщений")
                
        except Exception as e:
            logger.error(f"Ошибка очистки старых сообщений: {e}")


# Синглтон для глобального доступа
_lazy_memory_instance = None

def get_lazy_memory() -> LazyMemory:
    """Получает глобальный экземпляр LazyMemory"""
    global _lazy_memory_instance
    if _lazy_memory_instance is None:
        _lazy_memory_instance = LazyMemory()
    return _lazy_memory_instance 