"""
Модуль для работы с эмбеддингами.
"""
import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
import aiohttp

from config import EMBEDDING_CONFIG, EMBEDDING_API_KEY

logger = logging.getLogger("chatumba.embeddings")

class EmbeddingGenerator:
    """
    Класс для генерации эмбеддингов текста.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализирует генератор эмбеддингов.
        
        Args:
            api_key: API ключ для OpenAI
        """
        self.api_key = api_key or EMBEDDING_API_KEY
        self.model = EMBEDDING_CONFIG["model"]
        self.dimensions = EMBEDDING_CONFIG["dimensions"]
        self.local_fallback = EMBEDDING_CONFIG["local_fallback"]
        
        # Флаг, указывающий, используем ли мы локальную модель
        self.use_local = not self.api_key or self.api_key == "your_openai_api_key"
        
        if self.use_local:
            logger.warning("API ключ для эмбеддингов не указан, используем локальную модель")
            try:
                # Импортируем sentence-transformers только если нужно
                from sentence_transformers import SentenceTransformer
                self.local_model = SentenceTransformer(self.local_fallback)
                logger.info(f"Локальная модель {self.local_fallback} загружена успешно")
            except ImportError:
                logger.error("Не удалось импортировать sentence-transformers. Установите библиотеку: pip install sentence-transformers")
                self.local_model = None
            except Exception as e:
                logger.error(f"Ошибка при загрузке локальной модели: {e}")
                self.local_model = None
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Генерирует эмбеддинг для текста.
        
        Args:
            text: Текст для эмбеддинга
            
        Returns:
            Эмбеддинг в виде списка чисел или None в случае ошибки
        """
        if self.use_local:
            return self._generate_local_embedding(text)
        else:
            return await self._generate_openai_embedding(text)
    
    def _generate_local_embedding(self, text: str) -> Optional[List[float]]:
        """
        Генерирует эмбеддинг с помощью локальной модели.
        
        Args:
            text: Текст для эмбеддинга
            
        Returns:
            Эмбеддинг в виде списка чисел или None в случае ошибки
        """
        if not self.local_model:
            logger.error("Локальная модель не инициализирована")
            return None
        
        try:
            # Генерируем эмбеддинг
            embedding = self.local_model.encode(text)
            
            # Преобразуем в список
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Ошибка при генерации локального эмбеддинга: {e}")
            return None
    
    async def _generate_openai_embedding(self, text: str) -> Optional[List[float]]:
        """
        Генерирует эмбеддинг с помощью OpenAI API.
        
        Args:
            text: Текст для эмбеддинга
            
        Returns:
            Эмбеддинг в виде списка чисел или None в случае ошибки
        """
        url = "https://api.openai.com/v1/embeddings"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "input": text,
            "model": self.model
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ошибка OpenAI API: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
                    
                    # Извлекаем эмбеддинг
                    if "data" in result and len(result["data"]) > 0:
                        return result["data"][0]["embedding"]
                    
                    logger.error(f"Неожиданный формат ответа от OpenAI API: {result}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка при запросе к OpenAI API: {e}")
            return None


# Глобальный экземпляр для singleton pattern
_embedding_generator_instance = None


def get_embedding_generator() -> Optional[EmbeddingGenerator]:
    """
    Получает глобальный экземпляр EmbeddingGenerator (singleton pattern)
    
    Returns:
        EmbeddingGenerator или None если не инициализирован
    """
    global _embedding_generator_instance
    return _embedding_generator_instance


def init_embedding_generator(api_key: Optional[str] = None) -> EmbeddingGenerator:
    """
    Инициализирует глобальный экземпляр EmbeddingGenerator
    
    Args:
        api_key: API ключ для OpenAI (опционально)
        
    Returns:
        EmbeddingGenerator: Инициализированный экземпляр
    """
    global _embedding_generator_instance
    _embedding_generator_instance = EmbeddingGenerator(api_key)
    return _embedding_generator_instance