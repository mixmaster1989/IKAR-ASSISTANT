"""
Модуль для генерации изображений через DeepAI API.
"""
import asyncio
import time
import logging
import aiohttp
import os
from typing import Optional, Dict, Any
import json
import re
from pathlib import Path

# Абсолютные импорты
try:
    from backend.config import *
except ImportError:
    # Fallback для прямого запуска
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config import *

logger = logging.getLogger(__name__)

# Fallback для переменных окружения
try:
    DEEPAI_API_KEY
except NameError:
    DEEPAI_API_KEY = os.environ.get("DEEPAI_API_KEY", "")

# DeepAI API конфигурация
DEEPAI_BASE_URL = "https://api.deepai.org/api"
DEEPAI_DEFAULT_MODEL = "text2img"

# Доступные модели DeepAI
DEEPAI_MODELS = {
    "text2img": {
        "name": "Text to Image",
        "description": "Генерация изображений из текста",
        "endpoint": "/text2img",
        "supports_size": True,
        "max_size": 1024,
        "free_tier": True
    },
    "tor-sr": {
        "name": "Super Resolution",
        "description": "Улучшение разрешения изображений",
        "endpoint": "/tor-sr",
        "supports_size": False,
        "free_tier": True
    },
    "colorizer": {
        "name": "Colorizer",
        "description": "Раскрашивание черно-белых фотографий",
        "endpoint": "/colorizer",
        "supports_size": False,
        "free_tier": True
    },
    "deepdream": {
        "name": "DeepDream",
        "description": "Художественная обработка изображений",
        "endpoint": "/deepdream",
        "supports_size": False,
        "free_tier": True
    },
    "waifu2x": {
        "name": "Waifu2x",
        "description": "Улучшение аниме изображений",
        "endpoint": "/waifu2x",
        "supports_size": False,
        "free_tier": True
    }
}

async def generate_image_deepai(
    prompt: str,
    model: str = DEEPAI_DEFAULT_MODEL,
    width: int = 512,
    height: int = 512,
    timeout: int = 300  # 5 минут таймаут
) -> Optional[bytes]:
    """
    Генерирует изображение через DeepAI API
    
    Args:
        prompt: Текстовый промпт для генерации
        model: Модель для использования
        width: Ширина изображения
        height: Высота изображения
        timeout: Таймаут ожидания в секундах
        
    Returns:
        bytes: Изображение в формате bytes или None при ошибке
    """
    
    if not DEEPAI_API_KEY:
        logger.error("❌ DEEPAI_API_KEY не найден в переменных окружения")
        return None
    
    if model not in DEEPAI_MODELS:
        logger.warning(f"⚠️ Модель {model} не найдена, используем {DEEPAI_DEFAULT_MODEL}")
        model = DEEPAI_DEFAULT_MODEL
    
    model_info = DEEPAI_MODELS[model]
    endpoint = model_info["endpoint"]
    
    logger.info(f"🎨 Генерация изображения через DeepAI: '{prompt[:50]}...' (модель: {model})")
    
    # Подготовка данных для запроса
    data = {
        "text": prompt
    }
    
    # Добавляем размер для поддерживаемых моделей
    if model_info["supports_size"]:
        data["width"] = str(width)
        data["height"] = str(height)
    
    headers = {
        "api-key": DEEPAI_API_KEY,
        "User-Agent": "ChatumbaAI/1.0"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Отправляем запрос на генерацию
            async with session.post(
                f"{DEEPAI_BASE_URL}{endpoint}",
                headers=headers,
                data=data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка DeepAI API: {response.status} - {error_text}")
                    return None
                
                result = await response.json()
                
                # Получаем URL изображения из ответа
                image_url = result.get("output_url")
                if not image_url:
                    logger.error(f"❌ URL изображения не найден в ответе: {result}")
                    return None
                
                logger.info(f"🎉 Изображение готово! Загружаем: {image_url}")
                
                # Загружаем изображение
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as img_response:
                    if img_response.status == 200:
                        image_data = await img_response.read()
                        logger.info(f"✅ Изображение успешно загружено ({len(image_data)} bytes)")
                        return image_data
                    else:
                        logger.error(f"❌ Ошибка загрузки изображения: {img_response.status}")
                        return None
    
    except asyncio.TimeoutError:
        logger.error("❌ Таймаут запроса к DeepAI API")
        return None
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {str(e)}")
        return None

async def get_deepai_models() -> Dict[str, Dict[str, Any]]:
    """
    Возвращает информацию о доступных моделях DeepAI
    
    Returns:
        dict: Словарь с информацией о моделях
    """
    return DEEPAI_MODELS

def get_available_models() -> Dict[str, Dict[str, Any]]:
    """
    Возвращает словарь доступных моделей с описаниями
    
    Returns:
        dict: Словарь моделей с метаданными
    """
    models = {}
    
    for model_id, model_info in DEEPAI_MODELS.items():
        models[model_id] = {
            "name": model_info["name"],
            "type": "deepai",
            "description": model_info["description"],
            "max_resolution": model_info.get("max_size", 512),
            "supports_nsfw": False,  # DeepAI не поддерживает NSFW
            "average_wait_time": "10-30 seconds",
            "free": model_info.get("free_tier", True)
        }
    
    return models

async def image_generator(
    prompt: str,
    model: str = DEEPAI_DEFAULT_MODEL,
    width: int = 512,
    height: int = 512,
    timeout: int = 300,
    **kwargs
) -> Optional[bytes]:
    """
    Основная функция генерации изображений через DeepAI
    
    Args:
        prompt: Текстовый промпт
        model: Модель для использования
        width: Ширина изображения
        height: Высота изображения
        timeout: Таймаут ожидания
        **kwargs: Дополнительные параметры
        
    Returns:
        bytes: Изображение в формате bytes
    """
    
    # Проверяем доступность модели
    if model not in DEEPAI_MODELS:
        logger.warning(f"⚠️ Модель {model} не найдена, используем {DEEPAI_DEFAULT_MODEL}")
        model = DEEPAI_DEFAULT_MODEL
    
    # Генерируем изображение
    return await generate_image_deepai(
        prompt=prompt,
        model=model,
        width=width,
        height=height,
        timeout=timeout
    )

async def translate_prompt_to_english(prompt: str) -> str:
    """
    Переводит и улучшает промпт на английский язык через OpenRouter LLM
    Args:
        prompt: Исходный промпт (обычно на русском)
    Returns:
        str: Качественный промпт на английском для text-to-image
    """
    # Если промпт уже на английском, возвращаем как есть
    if not any(ord(char) > 127 for char in prompt):
        return prompt
    
    # Используем LLM клиент из менеджера
    try:
        from utils.component_manager import get_component_manager
        component_manager = get_component_manager()
        local_llm_client = component_manager.get_llm_client()
    except ImportError:
        logger.error("Failed to import ComponentManager, returning original prompt")
        return prompt
    
    system_prompt = (
        "You are a prompt engineer for text-to-image models. Your job is to translate the user's Russian request to English for image generation. "
        "Strictly preserve all key details, numbers, objects, actions, and relationships from the original prompt. "
        "Do NOT add, remove, or change the number of people, animals, or objects. Do NOT reinterpret, generalize, or average the request. "
        "You may add a few stylistic details (lighting, style, quality) ONLY if they do not change the meaning. "
        "Output strictly in JSON: {\"prompt\": \"...\"} with no extra text.\n"
        "Examples:\n"
        "Input: 'три человека и две собаки на пляже'\nOutput: {\"prompt\": \"three people and two dogs standing on a beach, photorealistic, high quality\"}\n"
        "Input: 'девушка держит в руках красную книгу'\nOutput: {\"prompt\": \"a girl holding a red book, detailed, soft lighting\"}"
    )
    
    try:
        improved_response = await local_llm_client.chat_completion(
            user_message=prompt,
            system_prompt=system_prompt,
            max_tokens=200,
            temperature=0.7
        )
        if improved_response:
            # Пытаемся найти и распарсить JSON с ключом prompt
            match = re.search(r'\{[^{}]*"prompt"\s*:\s*".*?"[^{}]*\}', improved_response, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    if isinstance(data, dict) and "prompt" in data:
                        logger.info(f"[PROMPT TRANSLATE] Итоговый английский промпт: {data['prompt'].strip()}")
                        return data["prompt"].strip()
                except Exception as e:
                    logger.error(f"[PROMPT TRANSLATE] Ошибка парсинга JSON: {e}")
            logger.error(f"[PROMPT TRANSLATE] Не удалось найти корректный JSON с ключом 'prompt' в ответе: {improved_response}")
            return prompt
        else:
            return prompt
    except Exception as e:
        logger.error(f"[PROMPT TRANSLATE] Ошибка при обращении к OpenRouter: {e}")
    return prompt

# Функции для обратной совместимости
async def generate_image_stable_horde(prompt: str, model: str = DEEPAI_DEFAULT_MODEL, **kwargs) -> Optional[bytes]:
    """Обратная совместимость с Stable Horde API"""
    return await image_generator(prompt, model, **kwargs)

async def generate_image_hf(prompt: str, model: str = DEEPAI_DEFAULT_MODEL, **kwargs) -> Optional[bytes]:
    """Обратная совместимость с HuggingFace API"""
    return await image_generator(prompt, model, **kwargs)

async def generate_image_replicate(prompt: str, model: str = DEEPAI_DEFAULT_MODEL, **kwargs) -> Optional[bytes]:
    """Обратная совместимость с Replicate API"""
    return await image_generator(prompt, model, **kwargs)

if __name__ == "__main__":
    # Тестовый запуск
    async def test():
        result = await image_generator("a beautiful sunset over the ocean")
        if result:
            print(f"✅ Тест успешен! Получено изображение размером {len(result)} bytes")
        else:
            print("❌ Тест не удался")
    
    asyncio.run(test()) 