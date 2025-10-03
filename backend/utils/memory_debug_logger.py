"""
🧠 Специальный логгер для отладки работы системы памяти
Детально логирует весь процесс обработки запросов к боту
"""

import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class MemoryDebugLogger:
    """Специализированный логгер для отладки памяти"""
    
    def __init__(self):
        self.log_file = Path("logs/memory_debug.log")
        self.setup_logger()
        self.current_request_id = None
        self.request_start_time = None
        
    def setup_logger(self):
        """Настройка специального логгера"""
        # Создаем уникальный логгер для отладки памяти
        self.logger = logging.getLogger('memory_debug')
        self.logger.setLevel(logging.DEBUG)
        
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Создаем форматтер с максимальной детализацией
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-15s | %(funcName)-20s:%(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )
        
        # Файловый обработчик
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Консольный обработчик для важных событий
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '🧠 %(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.propagate = False
        
    def start_request(self, user_id: str, chat_id: str, message: str) -> str:
        """Начинает логирование нового запроса"""
        self.current_request_id = f"req_{int(time.time() * 1000)}_{user_id[-4:]}"
        self.request_start_time = time.time()
        
        self.logger.info("=" * 100)
        self.logger.info(f"🚀 НАЧАЛО ОБРАБОТКИ ЗАПРОСА | ID: {self.current_request_id}")
        self.logger.info(f"👤 User ID: {user_id}")
        self.logger.info(f"💬 Chat ID: {chat_id}")
        self.logger.info(f"📝 Message: {message[:200]}{'...' if len(message) > 200 else ''}")
        self.logger.info("-" * 100)
        
        return self.current_request_id
    
    def log_trigger_bot(self, trigger_type: str, details: Dict[str, Any]):
        """Логирует срабатывание триггера бота"""
        self.logger.info(f"🎯 BOT TRIGGER | Type: {trigger_type}")
        self.logger.debug(f"   Details: {json.dumps(details, ensure_ascii=False, indent=2)}")
    
    def log_lazy_memory_start(self, user_id: str, query: str):
        """Логирует начало работы LazyMemory"""
        self.logger.info(f"🔍 LAZY MEMORY | Start search for user: {user_id}")
        self.logger.debug(f"   Query: {query}")
    
    def log_lazy_memory_cache(self, cache_hit: bool, cache_key: str):
        """Логирует работу кэша LazyMemory"""
        status = "HIT" if cache_hit else "MISS"
        self.logger.debug(f"💾 LAZY MEMORY CACHE | {status} | Key: {cache_key}")
    
    def log_lazy_memory_keywords(self, keywords: List[str]):
        """Логирует извлечённые ключевые слова"""
        self.logger.debug(f"🔑 LAZY MEMORY KEYWORDS | Found: {keywords}")
    
    def log_lazy_memory_results(self, results_count: int, results: List[Dict[str, Any]]):
        """Логирует результаты поиска LazyMemory"""
        self.logger.info(f"📊 LAZY MEMORY RESULTS | Found: {results_count} messages")
        
        for i, result in enumerate(results[:3], 1):  # Показываем первые 3
            content_preview = result.get('content', '')[:100]
            timestamp = result.get('timestamp', 'unknown')
            self.logger.debug(f"   {i}. [{timestamp}] {content_preview}...")
    
    def log_memory_injector_start(self, query: str, context: str, user_id: Optional[str]):
        """Логирует начало работы MemoryInjector"""
        self.logger.info(f"💉 MEMORY INJECTOR | Start injection")
        self.logger.debug(f"   Query: {query[:150]}{'...' if len(query) > 150 else ''}")
        self.logger.debug(f"   Context: {context[:100]}{'...' if len(context) > 100 else ''}")
        self.logger.debug(f"   User ID: {user_id}")
    
    def log_memory_injector_keywords(self, query_keywords: List[str], context_keywords: List[str]):
        """Логирует ключевые слова инъектора"""
        self.logger.debug(f"🔑 INJECTOR KEYWORDS | Query: {query_keywords}")
        self.logger.debug(f"🔑 INJECTOR KEYWORDS | Context: {context_keywords}")
    
    def log_collective_wisdom_search(self, keyword: str, limit: int):
        """Логирует поиск в коллективной мудрости"""
        self.logger.debug(f"🧠 COLLECTIVE WISDOM | Search: '{keyword}' (limit: {limit})")
    
    def log_collective_wisdom_results(self, keyword: str, results_count: int, results: List[Any]):
        """Логирует результаты поиска коллективной мудрости"""
        self.logger.debug(f"🧠 COLLECTIVE WISDOM RESULTS | '{keyword}': {results_count} memories")
        
        for i, result in enumerate(results[:2], 1):  # Показываем первые 2
            content_preview = getattr(result, 'content', '')[:80]
            importance = getattr(result, 'importance', 0)
            memory_type = getattr(result, 'memory_type', 'unknown')
            self.logger.debug(f"   {i}. [{memory_type}] Importance: {importance:.2f} | {content_preview}...")
    
    def log_relevance_calculation(self, memory_id: str, relevance_score: float, threshold: float):
        """Логирует расчёт релевантности"""
        passed = "✅" if relevance_score > threshold else "❌"
        self.logger.debug(f"📈 RELEVANCE | {passed} Memory {memory_id}: {relevance_score:.3f} (threshold: {threshold})")
    
    def log_memory_chunks_selection(self, total_chunks: int, selected_chunks: int, token_budget: int):
        """Логирует выбор чанков памяти"""
        self.logger.info(f"📦 MEMORY CHUNKS | Selected: {selected_chunks}/{total_chunks} (budget: {token_budget} tokens)")
    
    def log_memory_chunk_details(self, chunk_index: int, chunk_type: str, relevance: float, tokens: int, content_preview: str):
        """Логирует детали чанка памяти"""
        self.logger.debug(f"   📄 Chunk {chunk_index+1}: [{chunk_type}] Rel: {relevance:.3f} | Tokens: {tokens} | {content_preview[:80]}...")
    
    def log_memory_injection_result(self, original_tokens: int, injected_tokens: int, chunks_used: int):
        """Логирует результат инъекции памяти"""
        total_tokens = original_tokens + injected_tokens
        memory_ratio = (injected_tokens / total_tokens * 100) if total_tokens > 0 else 0
        
        self.logger.info(f"✅ MEMORY INJECTION | Used {chunks_used} chunks | Memory: {injected_tokens} tokens ({memory_ratio:.1f}%)")
        self.logger.debug(f"   Original prompt: {original_tokens} tokens")
        self.logger.debug(f"   Final prompt: {total_tokens} tokens")
    
    def log_no_memory_injection(self, reason: str):
        """Логирует случаи, когда память не инъектируется"""
        self.logger.info(f"⚠️ NO MEMORY INJECTION | Reason: {reason}")
    
    def end_request(self, success: bool = True):
        """Завершает логирование запроса"""
        if self.request_start_time:
            duration = time.time() - self.request_start_time
            status = "✅ SUCCESS" if success else "❌ FAILED"
            
            self.logger.info("-" * 100)
            self.logger.info(f"🏁 КОНЕЦ ОБРАБОТКИ | {status} | Duration: {duration:.3f}s | ID: {self.current_request_id}")
            self.logger.info("=" * 100)
            self.logger.info("")  # Пустая строка для разделения
        
        self.current_request_id = None
        self.request_start_time = None
    
    def log_error(self, component: str, error: Exception, details: Dict[str, Any] = None):
        """Логирует ошибки в компонентах"""
        self.logger.error(f"💥 ERROR in {component} | {type(error).__name__}: {str(error)}")
        if details:
            self.logger.error(f"   Details: {json.dumps(details, ensure_ascii=False, indent=2)}")

# Синглтон для глобального доступа
_memory_debug_logger = None

def get_memory_debug_logger() -> MemoryDebugLogger:
    """Получить экземпляр логгера отладки памяти"""
    global _memory_debug_logger
    if _memory_debug_logger is None:
        _memory_debug_logger = MemoryDebugLogger()
    return _memory_debug_logger

def enable_memory_debug_logging():
    """Включить детальное логирование памяти"""
    logger = get_memory_debug_logger()
    logger.logger.info("🔧 MEMORY DEBUG LOGGING ENABLED")
    return logger

def disable_memory_debug_logging():
    """Отключить детальное логирование памяти"""
    global _memory_debug_logger
    if _memory_debug_logger:
        _memory_debug_logger.logger.info("🔧 MEMORY DEBUG LOGGING DISABLED")
        # Удаляем обработчики
        for handler in _memory_debug_logger.logger.handlers:
            _memory_debug_logger.logger.removeHandler(handler)
        _memory_debug_logger = None