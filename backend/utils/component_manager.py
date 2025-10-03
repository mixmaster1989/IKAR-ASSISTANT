"""
Централизованный менеджер компонентов системы.
Обеспечивает единственный экземпляр каждого компонента для избежания множественной инициализации.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys
import os

# Добавляем путь к backend в sys.path для корректных импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class ComponentManager:
    """
    Синглтон-менеджер для централизованного управления компонентами системы.
    Гарантирует единственный экземпляр каждого компонента.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Компоненты системы
            self._sqlite_storage = None
            self._llm_client = None
            self._embedding_generator = None
            self._vector_store = None
            self._config = None
            
            # Флаги инициализации
            self._components_initialized = {
                'sqlite_storage': False,
                'llm_client': False,
                'embedding_generator': False,
                'vector_store': False,
                'config': False
            }
            
            self._initialized = True
            logger.debug("ComponentManager инициализирован")
    
    def get_config(self):
        """Получает экземпляр конфигурации"""
        if not self._components_initialized['config']:
            from config import Config
            self._config = Config()
            self._components_initialized['config'] = True
            logger.debug("Config инициализирован")
        return self._config
    
    def get_sqlite_storage(self):
        """Получает экземпляр SQLite хранилища"""
        if not self._components_initialized['sqlite_storage']:
            from memory.sqlite import SQLiteStorage
            self._sqlite_storage = SQLiteStorage()
            self._components_initialized['sqlite_storage'] = True
            logger.debug("SQLiteStorage инициализирован")
        return self._sqlite_storage
    
    def get_llm_client(self):
        """Получает экземпляр LLM клиента"""
        if not self._components_initialized['llm_client']:
            from llm import OpenRouterClient
            config = self.get_config()
            self._llm_client = OpenRouterClient(config)
            self._components_initialized['llm_client'] = True
            logger.debug("OpenRouterClient инициализирован")
        return self._llm_client
    
    def get_embedding_generator(self):
        """Получает экземпляр генератора эмбеддингов"""
        if not self._components_initialized['embedding_generator']:
            from memory.embeddings import EmbeddingGenerator
            self._embedding_generator = EmbeddingGenerator()
            self._components_initialized['embedding_generator'] = True
            logger.debug("EmbeddingGenerator инициализирован")
        return self._embedding_generator
    
    def get_lazy_memory(self):
        """Получает экземпляр LazyMemory (замена VectorStore)"""
        if not self._components_initialized.get('lazy_memory', False):
            from memory.lazy_memory import get_lazy_memory
            self._lazy_memory = get_lazy_memory()
            self._components_initialized['lazy_memory'] = True
            logger.debug("LazyMemory инициализирован")
        return self._lazy_memory
    
    def get_vector_store(self):
        """Получает экземпляр векторного хранилища (устаревший)"""
        # Возвращаем LazyMemory для обратной совместимости
        return self.get_lazy_memory()
    
    def get_all_components(self) -> Dict[str, Any]:
        """Получает все основные компоненты системы"""
        return {
            'config': self.get_config(),
            'sqlite_storage': self.get_sqlite_storage(),
            'llm_client': self.get_llm_client(),
            'embedding_generator': self.get_embedding_generator(),
            'vector_store': self.get_vector_store()
        }
    
    def get_initialization_status(self) -> Dict[str, bool]:
        """Возвращает статус инициализации всех компонентов"""
        return self._components_initialized.copy()
    
    def reset(self):
        """Сбрасывает все компоненты (для тестирования)"""
        self._sqlite_storage = None
        self._llm_client = None
        self._embedding_generator = None
        self._vector_store = None
        self._config = None
        
        for key in self._components_initialized:
            self._components_initialized[key] = False
        
        logger.debug("ComponentManager сброшен")


# Глобальный экземпляр менеджера компонентов
_component_manager = None

def get_component_manager() -> ComponentManager:
    """Получает глобальный экземпляр менеджера компонентов"""
    global _component_manager
    if _component_manager is None:
        _component_manager = ComponentManager()
    return _component_manager 