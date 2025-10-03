"""
Модуль для обработки изображений в Telegram боте.
"""
import logging
import os
import uuid
from typing import Optional, Dict, Any, List
from pathlib import Path

from vision.image_analyzer import ImageAnalyzer

logger = logging.getLogger("chatumba.telegram.vision")

# Глобальный экземпляр анализатора изображений
image_analyzer = None

def get_image_analyzer() -> ImageAnalyzer:
    """Получает или создает экземпляр анализатора изображений."""
    global image_analyzer
    if image_analyzer is None:
        image_analyzer = ImageAnalyzer()
    return image_analyzer

async def process_telegram_photo(message: Dict[str, Any], chat_id: str, user_id: str, temp_dir: Path, download_telegram_file, send_telegram_message) -> Optional[str]:
    """
    Обрабатывает фото из Telegram.
    
    Args:
        message: Сообщение из Telegram
        chat_id: ID чата
        user_id: ID пользователя
        temp_dir: Директория для временных файлов
        download_telegram_file: Функция для скачивания файлов из Telegram
        send_telegram_message: Функция для отправки сообщений в Telegram
        
    Returns:
        Описание изображения или None при ошибке
    """
    try:
        # Получаем список фотографий (разные размеры)
        photos = message.get("photo", [])
        if not photos:
            logger.warning(f"Сообщение не содержит фотографий: {message}")
            return None
        
        # Берем самую большую фотографию (последнюю в списке)
        photo = photos[-1]
        file_id = photo.get("file_id")
        
        if not file_id:
            logger.warning(f"Не удалось получить file_id фотографии: {photo}")
            return None
        
        logger.info(f"Получено фото от {chat_id}, file_id: {file_id}")
        
        # Отправляем сообщение о начале обработки
        await send_telegram_message(chat_id, "🔍 Анализирую изображение...")
        
        # Скачиваем фото
        local_path = await download_telegram_file(file_id)
        
        if not local_path:
            logger.error(f"Не удалось скачать фото: {file_id}")
            await send_telegram_message(chat_id, "❌ Не удалось скачать фото для анализа.")
            return None
        
        # Анализируем изображение
        analyzer = get_image_analyzer()
        
        # Определяем промпт в зависимости от типа чата
        chat_type = message["chat"].get("type", "private")
        if chat_type in ("group", "supergroup"):
            prompt = "Что на этом изображении? Опиши подробно, но кратко. Используй русский язык."
        else:
            prompt = "Что на этом изображении? Опиши подробно, обращая внимание на детали. Используй русский язык."
        
        # Анализируем изображение напрямую из файла
        description = await analyzer.analyze_image(local_path, prompt)
        
        if not description:
            logger.error(f"Не удалось проанализировать изображение: {file_id}")
            await send_telegram_message(chat_id, "❌ Не удалось проанализировать изображение.")
            return None
        
        # Отправляем результат анализа
        await send_telegram_message(chat_id, f"👁️ <b>Я вижу на изображении:</b>\n\n{description}", "HTML")
        
        # Удаляем временный файл
        try:
            os.remove(local_path)
            logger.info(f"Удален временный файл: {local_path}")
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {e}")
        
        logger.info(f"[VISION] Возвращаю описание: {description[:100]}...")
        # Возвращаем описание изображения
        return description
        
    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}")
        await send_telegram_message(chat_id, "❌ Произошла ошибка при обработке изображения.")
        return None