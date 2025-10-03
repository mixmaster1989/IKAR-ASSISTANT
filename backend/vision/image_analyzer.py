"""
Модуль для анализа изображений с помощью мультимодальных моделей.
"""
import logging
import aiohttp
import json
from typing import Optional, Dict, Any, List

from config import OPENROUTER_API_KEYS
from vision.local_vision import LocalVisionAnalyzer

logger = logging.getLogger("chatumba.vision")

class ImageAnalyzer:
    """
    Класс для анализа изображений с помощью мультимодальных моделей через OpenRouter.
    """
    
    def __init__(self):
        """
        Инициализирует анализатор изображений.
        """
        self.api_keys = OPENROUTER_API_KEYS.copy()
        # Убираем пустые ключи
        self.api_keys = [key for key in self.api_keys if key and key != "your_openrouter_api_key"]
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "qwen/qwen2.5-vl-72b-instruct:free"
        
        # Инициализируем локальный анализатор как fallback
        self.local_analyzer = LocalVisionAnalyzer()
        
        if not self.api_keys:
            logger.warning("API ключи для OpenRouter не указаны!")
    
    async def analyze_image(self, image_path: str, prompt: str = "Что на этом изображении? Опиши подробно.") -> Optional[str]:
        """
        Анализирует изображение по пути с помощью мультимодальной модели.
        
        Args:
            image_path: Путь к изображению (локальный файл)
            prompt: Текстовый запрос для модели
            
        Returns:
            Текстовое описание изображения или None в случае ошибки
        """
        if not self.api_keys:
            logger.error("Нет доступных API ключей для анализа изображения")
            return None
        
        # Конвертируем изображение в base64
        try:
            import base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                
            # Формируем сообщения для модели с base64
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            # Пробуем основную модель
            for api_key in self.api_keys:
                result = await self._try_analyze_with_key(messages, api_key, self.model)
                if result:
                    return result
            
            # Пробуем альтернативную модель
            fallback_model = "anthropic/claude-3-haiku:free"
            logger.info(f"Пробуем альтернативную модель: {fallback_model}")
            for api_key in self.api_keys:
                result = await self._try_analyze_with_key(messages, api_key, fallback_model)
                if result:
                    return result
            
            logger.info("API модели недоступны, используем локальный анализ")
            # Используем локальный анализатор как последний fallback
            local_result = await self.local_analyzer.analyze_image(image_path, prompt)
            if local_result:
                return f"[Локальный анализ] {local_result}"
            
            logger.error("Не удалось проанализировать изображение со всеми доступными методами")
            return "Не удалось проанализировать изображение. Возможно, превышен лимит запросов или формат изображения не поддерживается."
            
        except Exception as e:
            logger.error(f"Ошибка при подготовке изображения: {e}")
            return f"Ошибка при анализе изображения: {str(e)}"
    
    async def _try_analyze_with_key(self, messages: List[Dict[str, Any]], api_key: str, model: str) -> Optional[str]:
        """
        Пробует проанализировать изображение с конкретным API ключом и моделью.
        
        Args:
            messages: Сообщения для модели
            api_key: API ключ OpenRouter
            model: Название модели для использования
            
        Returns:
            Текстовое описание изображения или None в случае ошибки
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/chatumba/chatumba",
            "X-Title": "Chatumba AI Companion",
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 1000  # Ограничиваем длину ответа
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=data, timeout=60) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(f"Ключ {api_key[:8]}... недоступен (429), пробуем следующий: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        logger.info(f"Успешно проанализировано изображение с моделью {model}: {content[:100]}...")
                        return content
                    
                    logger.error(f"Неожиданный формат ответа от OpenRouter: {result}")
                    return None
        except Exception as e:
            if "timeout" in str(e).lower():
                logger.error(f"Таймаут при запросе к модели {model}")
            else:
                logger.error(f"Исключение при анализе изображения с моделью {model}: {e}")
            return None
            logger.error(f"Таймаут при запросе к модели {model}")
            return None
        except Exception as e:
            logger.error(f"Исключение при анализе изображения с моделью {model}: {e}")
            return None