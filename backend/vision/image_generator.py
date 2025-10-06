"""
Модуль для генерации изображений через Pollinations.ai (основной) и Hugging Face API (fallback).
"""
import asyncio
import time
import logging
import aiohttp
import os
import urllib.parse
import requests
from typing import Optional, Dict, Any
import json
import re

# Абсолютные импорты (исправляем ошибку относительного импорта)
try:
    from backend.config import *
except ImportError:
    # Fallback для прямого запуска
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config import *

# Removed circular import - llm_client will be created locally

logger = logging.getLogger(__name__)

# Fallback для переменных окружения (если config не загрузился)
try:
    HF_API_KEY
except NameError:
    HF_API_KEY = os.environ.get("HF_API_KEY", "")

# Pollinations.ai конфигурация (ОСНОВНОЙ ГЕНЕРАТОР)
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"
POLLINATIONS_DEFAULT_MODEL = "flux"

# Pollinations.ai модели (основные)
POLLINATIONS_MODELS = {
    "flux": {
        "name": "FLUX",
        "description": "FLUX - высокое качество, быстрая генерация",
        "supports_size": True,
        "max_size": 2048,
        "free_tier": True,
        "average_wait_time": "3-10 seconds",
        "tested_performance": {
            "response_time": "3.58s",
            "image_size": "50000+ bytes",
            "format": "PNG",
            "resolution": "1024x1024"
        }
    },
    "flux-dev": {
        "name": "FLUX Development",
        "description": "FLUX Development - экспериментальная версия",
        "supports_size": True,
        "max_size": 2048,
        "free_tier": True,
        "average_wait_time": "5-15 seconds"
    },
    "turbo": {
        "name": "FLUX Turbo",
        "description": "FLUX Turbo - быстрая генерация",
        "supports_size": True,
        "max_size": 1024,
        "free_tier": True,
        "average_wait_time": "2-5 seconds"
    },
    "nanobanana": {
        "name": "Nano Banana",
        "description": "Nano Banana - компактная модель",
        "supports_size": True,
        "max_size": 1024,
        "free_tier": True,
        "average_wait_time": "1-3 seconds"
    }
}

# Hugging Face API конфигурация (FALLBACK)
HF_BASE_URL = "https://api-inference.huggingface.co/models"
HF_DEFAULT_MODEL = "stabilityai/stable-diffusion-3-medium-diffusers"

# Доступные модели в Hugging Face (fallback)
HF_MODELS = {
    "stabilityai/stable-diffusion-3-medium-diffusers": {
        "name": "Stable Diffusion 3 Medium",
        "description": "Современная модель SD3 Medium - высокое качество, быстрая генерация",
        "supports_size": True,
        "max_size": 1024,
        "free_tier": True,
        "average_wait_time": "3-5 seconds",
        "tested_performance": {
            "response_time": "3.40s",
            "image_size": "30916 bytes",
            "format": "JPEG",
            "resolution": "512x512"
        }
    },
    "stabilityai/stable-diffusion-xl-base-1.0": {
        "name": "SDXL Base 1.0",
        "description": "SDXL Base 1.0 - высокое качество изображений, проверенная модель",
        "supports_size": True,
        "max_size": 1024,
        "free_tier": True,
        "average_wait_time": "5-10 seconds",
        "tested_performance": {
            "response_time": "4.93s",
            "image_size": "48767 bytes",
            "format": "JPEG",
            "resolution": "512x512"
        }
    },
    "black-forest-labs/FLUX.1-dev": {
        "name": "FLUX.1 Development",
        "description": "FLUX.1 для разработки - высокое качество, детализация",
        "supports_size": True,
        "max_size": 1024,
        "free_tier": True,
        "average_wait_time": "4-6 seconds",
        "tested_performance": {
            "response_time": "4.20s",
            "image_size": "35000 bytes",
            "format": "JPEG",
            "resolution": "512x512"
        }
    },
    "black-forest-labs/FLUX.1-schnell": {
        "name": "FLUX.1 Schnell",
        "description": "FLUX.1 быстрая - быстрое создание изображений",
        "supports_size": True,
        "max_size": 1024,
        "free_tier": True,
        "average_wait_time": "2-4 seconds",
        "tested_performance": {
            "response_time": "2.70s",
            "image_size": "32000 bytes",
            "format": "JPEG",
            "resolution": "512x512"
        }
    }
}

async def generate_image_pollinations(
    prompt: str,
    model: str = POLLINATIONS_DEFAULT_MODEL,
    width: int = 1024,
    height: int = 1024,
    seed: Optional[int] = None,
    enhance: bool = True,
    safe: bool = True,
    timeout: int = 300
) -> Optional[bytes]:
    """
    Генерирует изображение через Pollinations.ai (ОСНОВНОЙ ГЕНЕРАТОР)
    
    Args:
        prompt: Текстовый промпт
        model: Модель для использования
        width: Ширина изображения
        height: Высота изображения
        seed: Сид для детерминированного результата
        enhance: Автопрокачка промпта LLM'ом
        safe: Строгий NSFW-фильтр
        timeout: Таймаут ожидания
        
    Returns:
        bytes: Изображение в формате bytes
    """
    
    logger.info(f"🎨 [POLLINATIONS] Генерируем изображение: {prompt[:50]}...")
    logger.info(f"🤖 [POLLINATIONS] Модель: {model}, размер: {width}x{height}")
    
    try:
        # URL-кодируем промпт
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Формируем URL
        url = f"{POLLINATIONS_BASE_URL}/{encoded_prompt}"
        
        # Параметры
        params = {
            "width": width,
            "height": height,
            "model": model,
            "enhance": "true" if enhance else "false",
            "safe": "true" if safe else "false"
        }
        
        if seed:
            params["seed"] = seed
        
        start_time = time.time()
        
        # Отправляем запрос
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    image_data = await response.read()
                    end_time = time.time()
                    
                    logger.info(f"✅ [POLLINATIONS] Изображение сгенерировано за {end_time - start_time:.2f}s, размер: {len(image_data)} bytes")
                    return image_data
                else:
                    logger.error(f"❌ [POLLINATIONS] Ошибка API: {response.status}")
                    return None
                    
    except asyncio.TimeoutError:
        logger.error(f"❌ [POLLINATIONS] Таймаут генерации ({timeout}s)")
        return None
    except Exception as e:
        logger.error(f"❌ [POLLINATIONS] Ошибка: {e}")
        return None

async def generate_image_huggingface(
    prompt: str,
    model: str = HF_DEFAULT_MODEL,
    width: int = 512,
    height: int = 512,
    timeout: int = 300
) -> Optional[bytes]:
    """
    Генерирует изображение через Hugging Face API (FALLBACK)
    
    Args:
        prompt: Текстовый промпт
        model: Модель для использования
        width: Ширина изображения
        height: Высота изображения
        timeout: Таймаут ожидания
        
    Returns:
        bytes: Изображение в формате bytes
    """
    
    logger.info(f"🎨 [HUGGINGFACE] Генерируем изображение (fallback): {prompt[:50]}...")
    logger.info(f"🤖 [HUGGINGFACE] Модель: {model}, размер: {width}x{height}")
    
    # Проверяем доступность модели
    if model not in HF_MODELS:
        logger.warning(f"⚠️ [HUGGINGFACE] Модель {model} не найдена, используем {HF_DEFAULT_MODEL}")
        model = HF_DEFAULT_MODEL
    
    try:
        url = f"{HF_BASE_URL}/{model}"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        
        # Подготавливаем параметры для Hugging Face
        payload = {
            "inputs": prompt,
            "parameters": {
                "width": width,
                "height": height,
                "num_inference_steps": 20,
                "guidance_scale": 7.5
            }
        }
        
        start_time = time.time()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    image_data = await response.read()
                    end_time = time.time()
                    
                    logger.info(f"✅ [HUGGINGFACE] Изображение сгенерировано за {end_time - start_time:.2f}s, размер: {len(image_data)} bytes")
                    return image_data
                else:
                    error_text = await response.text()
                    logger.error(f"❌ [HUGGINGFACE] Ошибка API: {response.status} - {error_text}")
                    return None
                    
    except asyncio.TimeoutError:
        logger.error(f"❌ [HUGGINGFACE] Таймаут генерации ({timeout}s)")
        return None
    except Exception as e:
        logger.error(f"❌ [HUGGINGFACE] Ошибка: {e}")
        return None

async def get_available_models() -> Dict[str, Dict[str, Any]]:
    """
    Возвращает список доступных моделей (Pollinations + Hugging Face)
    """
    models = {}
    
    # Добавляем модели Pollinations (основные)
    for model_id, model_info in POLLINATIONS_MODELS.items():
        models[f"pollinations_{model_id}"] = {
            "name": f"Pollinations {model_info['name']}",
            "type": "pollinations",
            "description": model_info["description"],
            "max_resolution": model_info.get("max_size", 1024),
            "supports_nsfw": False,
            "average_wait_time": model_info.get("average_wait_time", "3-10 seconds"),
            "free": model_info.get("free_tier", True),
            "priority": "primary"  # Основной генератор
        }
    
    # Добавляем модели Hugging Face (fallback)
    for model_id, model_info in HF_MODELS.items():
        models[f"hf_{model_id}"] = {
            "name": f"HuggingFace {model_info['name']}",
            "type": "huggingface",
            "description": model_info["description"],
            "max_resolution": model_info.get("max_size", 512),
            "supports_nsfw": False,
            "average_wait_time": model_info.get("average_wait_time", "5-10 seconds"),
            "free": model_info.get("free_tier", True),
            "priority": "fallback"  # Fallback генератор
        }
    
    return models

async def image_generator(
    prompt: str,
    model: str = None,
    width: int = 1024,
    height: int = 512,
    timeout: int = 300,
    **kwargs
) -> Optional[bytes]:
    """
    Основная функция генерации изображений с автоматическим fallback
    
    Args:
        prompt: Текстовый промпт
        model: Модель для использования (если None, используется Pollinations)
        width: Ширина изображения
        height: Высота изображения
        timeout: Таймаут ожидания
        **kwargs: Дополнительные параметры
        
    Returns:
        bytes: Изображение в формате bytes
    """
    
    logger.info(f"🎨 [IMAGE_GENERATOR] Начинаем генерацию: {prompt[:50]}...")
    
    # Если модель не указана, используем Pollinations по умолчанию
    if model is None:
        model = f"pollinations_{POLLINATIONS_DEFAULT_MODEL}"
    
    # Определяем тип генератора по префиксу модели
    if model.startswith("pollinations_"):
        # Pollinations генератор
        pollinations_model = model.replace("pollinations_", "")
        
        if pollinations_model not in POLLINATIONS_MODELS:
            logger.warning(f"⚠️ [IMAGE_GENERATOR] Модель Pollinations {pollinations_model} не найдена, используем {POLLINATIONS_DEFAULT_MODEL}")
            pollinations_model = POLLINATIONS_DEFAULT_MODEL
        
        # Пробуем Pollinations
        image_data = await generate_image_pollinations(
            prompt=prompt,
            model=pollinations_model,
            width=width,
            height=height,
            timeout=timeout,
            **kwargs
        )
        
        if image_data:
            logger.info("✅ [IMAGE_GENERATOR] Pollinations успешно сгенерировал изображение")
            return image_data
        else:
            logger.warning("⚠️ [IMAGE_GENERATOR] Pollinations не смог сгенерировать, пробуем HuggingFace fallback")
    
    elif model.startswith("hf_"):
        # Hugging Face генератор
        hf_model = model.replace("hf_", "")
        
        if hf_model not in HF_MODELS:
            logger.warning(f"⚠️ [IMAGE_GENERATOR] Модель HuggingFace {hf_model} не найдена, используем {HF_DEFAULT_MODEL}")
            hf_model = HF_DEFAULT_MODEL
        
        image_data = await generate_image_huggingface(
            prompt=prompt,
            model=hf_model,
            width=width,
            height=height,
            timeout=timeout
        )
        
        if image_data:
            logger.info("✅ [IMAGE_GENERATOR] HuggingFace успешно сгенерировал изображение")
            return image_data
        else:
            logger.error("❌ [IMAGE_GENERATOR] HuggingFace не смог сгенерировать изображение")
            return None
    
    else:
        # Неизвестный формат модели, пробуем Pollinations по умолчанию
        logger.warning(f"⚠️ [IMAGE_GENERATOR] Неизвестный формат модели {model}, пробуем Pollinations")
        
        image_data = await generate_image_pollinations(
            prompt=prompt,
            model=POLLINATIONS_DEFAULT_MODEL,
            width=width,
            height=height,
            timeout=timeout,
            **kwargs
        )
        
        if image_data:
            logger.info("✅ [IMAGE_GENERATOR] Pollinations (fallback) успешно сгенерировал изображение")
            return image_data
        else:
            logger.warning("⚠️ [IMAGE_GENERATOR] Pollinations fallback не сработал, пробуем HuggingFace")
            
            # Последняя попытка через HuggingFace
            image_data = await generate_image_huggingface(
                prompt=prompt,
                model=HF_DEFAULT_MODEL,
                width=width,
                height=height,
                timeout=timeout
            )
            
            if image_data:
                logger.info("✅ [IMAGE_GENERATOR] HuggingFace (final fallback) успешно сгенерировал изображение")
                return image_data
            else:
                logger.error("❌ [IMAGE_GENERATOR] Все генераторы не смогли создать изображение")
                return None

# Обратная совместимость - старые функции
async def generate_image_stable_horde(prompt: str, model: str = HF_DEFAULT_MODEL, **kwargs) -> Optional[bytes]:
    """Обратная совместимость - перенаправляет на image_generator"""
    return await image_generator(prompt, f"hf_{model}", **kwargs)

async def generate_image_hf(prompt: str, model: str = HF_DEFAULT_MODEL, **kwargs) -> Optional[bytes]:
    """Обратная совместимость - перенаправляет на image_generator"""
    return await image_generator(prompt, f"hf_{model}", **kwargs)

async def generate_image_replicate(prompt: str, model: str = HF_DEFAULT_MODEL, **kwargs) -> Optional[bytes]:
    """Обратная совместимость - перенаправляет на image_generator"""
    return await image_generator(prompt, f"pollinations_{POLLINATIONS_DEFAULT_MODEL}", **kwargs)

async def generate_image_deepai(prompt: str, model: str = HF_DEFAULT_MODEL, **kwargs) -> Optional[bytes]:
    """Обратная совместимость - перенаправляет на image_generator"""
    return await image_generator(prompt, f"pollinations_{POLLINATIONS_DEFAULT_MODEL}", **kwargs)

# Функция для тестирования
async def test_image_generation():
    """Тестирует генерацию изображений"""
    logger.info("🧪 Тестируем генерацию изображений...")
    
    test_prompt = "a beautiful sunset over mountains"
    result = await image_generator(test_prompt)
    
    if result:
        logger.info(f"✅ Тест успешен! Размер изображения: {len(result)} bytes")
    else:
        logger.error("❌ Тест не прошел")

ARGOS_RU_EN_URL = "https://data.argosopentech.com/argospm/v1/translate-ru_en-1_9.argosmodel"
ARGOS_RU_EN_MODEL = "translate-ru_en-1_9.argosmodel"

async def translate_prompt_to_english(prompt: str) -> str:
    """
    Переводит промпт на английский язык через локальный Argos Translate.
    Если Argos не доступен, возвращает оригинальный промпт с предупреждением.
    
    Args:
        prompt: Исходный промпт (обычно на русском)
    Returns:
        str: Промпт на английском для text-to-image
    """
    if not any(ord(char) > 127 for char in prompt):
        logger.info(f"[PROMPT TRANSLATE] Промпт уже на английском: {prompt}")
        return prompt

    # Попытка локального перевода через Argos Translate
    try:
        import argostranslate.package, argostranslate.translate
        from pathlib import Path
        
        # Проверяем, установлена ли пара ru->en
        installed_languages = argostranslate.translate.get_installed_languages()
        from_lang = next((lang for lang in installed_languages if lang.code == "ru"), None)
        to_lang = next((lang for lang in installed_languages if lang.code == "en"), None)
        
        if not (from_lang and to_lang):
            # Скачиваем и устанавливаем языковую пару
            logger.info("[PROMPT TRANSLATE] Скачиваем языковую модель Argos ru->en...")
            try:
                import urllib.request
                import tempfile
                import os
                
                # Актуальный URL для модели ru->en с data.argosopentech.com
                model_url = "https://data.argosopentech.com/argospm/v1/translate-ru_en-1_9.argosmodel"
                
                # Создаем временный файл для скачивания
                with tempfile.NamedTemporaryFile(delete=False, suffix='.argosmodel') as tmp_file:
                    logger.info(f"[PROMPT TRANSLATE] Скачиваем модель с {model_url}...")
                    urllib.request.urlretrieve(model_url, tmp_file.name)
                    
                    # Устанавливаем модель
                    logger.info("[PROMPT TRANSLATE] Устанавливаем модель...")
                    argostranslate.package.install_from_path(tmp_file.name)
                    
                    # Удаляем временный файл
                    os.unlink(tmp_file.name)
                    
                    # Обновляем список языков
                    installed_languages = argostranslate.translate.get_installed_languages()
                    from_lang = next((lang for lang in installed_languages if lang.code == "ru"), None)
                    to_lang = next((lang for lang in installed_languages if lang.code == "en"), None)
                    
            except Exception as e:
                logger.warning(f"[PROMPT TRANSLATE] Не удалось скачать модель Argos: {e}")
                return prompt
        
        if from_lang and to_lang:
            # Выполняем перевод
            translated = argostranslate.translate.translate(prompt, from_lang, to_lang)
            logger.info(f"[PROMPT TRANSLATE] Переведено: '{prompt}' -> '{translated}'")
            return translated
        else:
            logger.warning("[PROMPT TRANSLATE] Языковая пара ru->en не найдена")
            return prompt
            
    except ImportError:
        logger.warning("[PROMPT TRANSLATE] Argos Translate не установлен, используем оригинальный промпт")
        return prompt
    except Exception as e:
        logger.warning(f"[PROMPT TRANSLATE] Ошибка перевода: {e}, используем оригинальный промпт")
        return prompt

if __name__ == "__main__":
    # Тестируем генерацию
    asyncio.run(test_image_generation())