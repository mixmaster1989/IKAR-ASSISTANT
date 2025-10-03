"""
Модуль для улучшенной отправки сообщений в Telegram с задержками и retry логикой.
"""

import asyncio
import aiohttp
from typing import Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Константы
TELEGRAM_MSG_LIMIT = 4000
MAX_RETRIES = 3
RETRY_DELAY = 1.0
PART_DELAY = 0.8


async def send_telegram_message_with_retry(chat_id: str, text: str, parse_mode: Optional[str] = None, token: str = None):
    """
    Отправляет сообщение в Telegram с retry логикой.
    
    Args:
        chat_id: ID чата
        text: Текст сообщения
        parse_mode: Режим парсинга (HTML, Markdown)
        token: Токен бота
    
    Returns:
        bool: True если отправлено успешно
    """
    if not token:
        logger.error("❌ Токен бота не предоставлен")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        data["parse_mode"] = parse_mode

    for attempt in range(MAX_RETRIES):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info(f"✅ Сообщение отправлено в чат {chat_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка отправки: {response.status} - {error_text}")
                        
                        # Обработка rate limiting
                        if response.status == 429:
                            wait_time = RETRY_DELAY * (2 ** attempt)
                            logger.warning(f"⏳ Rate limiting, ждем {wait_time}с (попытка {attempt + 1}/{MAX_RETRIES})")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        # Другие ошибки
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY)
                            continue
                        else:
                            return False
                            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке (попытка {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                return False
    
    return False


async def send_long_telegram_message_improved(chat_id: str, text: str, parse_mode: Optional[str] = None, token: str = None):
    """
    Улучшенная функция отправки длинных сообщений с задержками и retry логикой.
    
    Args:
        chat_id: ID чата
        text: Текст сообщения
        parse_mode: Режим парсинга
        token: Токен бота
    
    Returns:
        bool: True если все части отправлены успешно
    """
    if not token:
        logger.error("❌ Токен бота не предоставлен")
        return False
    
    # Разбиваем на части
    parts = []
    while text:
        if len(text) <= TELEGRAM_MSG_LIMIT:
            parts.append(text)
            break
        # Ищем ближайший разрыв строки до лимита
        split_idx = text.rfind('\n', 0, TELEGRAM_MSG_LIMIT)
        if split_idx == -1 or split_idx < TELEGRAM_MSG_LIMIT // 2:
            # Если нет нормального разрыва, режем по лимиту
            split_idx = TELEGRAM_MSG_LIMIT
        part = text[:split_idx].rstrip()
        parts.append(part)
        text = text[split_idx:].lstrip()
    
    total = len(parts)
    success_count = 0
    
    logger.info(f"[LONG MSG] Разбито на {total} частей")
    
    for idx, part in enumerate(parts, 1):
        logger.info(f"[LONG MSG] Отправка части {idx}/{total}, длина {len(part)} символов")
        
        # Retry логика для каждой части
        for retry_attempt in range(MAX_RETRIES):
            try:
                if await send_telegram_message_with_retry(chat_id, part, parse_mode, token):
                    success_count += 1
                    logger.info(f"[LONG MSG] ✅ Часть {idx}/{total} успешно отправлена")
                    break
                else:
                    logger.error(f"[LONG MSG] ❌ Ошибка отправки части {idx} (попытка {retry_attempt + 1}/{MAX_RETRIES})")
                    if retry_attempt == MAX_RETRIES - 1:
                        logger.error(f"[LONG MSG] ❌ Часть {idx} не удалось отправить после всех попыток")
                        break
                    else:
                        await asyncio.sleep(RETRY_DELAY)
                        
            except Exception as e:
                logger.error(f"[LONG MSG] ❌ Исключение при отправке части {idx} (попытка {retry_attempt + 1}/{MAX_RETRIES}): {e}")
                if retry_attempt == MAX_RETRIES - 1:
                    logger.error(f"[LONG MSG] ❌ Часть {idx} не удалось отправить после всех попыток")
                    break
                else:
                    await asyncio.sleep(RETRY_DELAY)
        
        # Задержка между частями (кроме последней)
        if idx < total:
            logger.info(f"[LONG MSG] ⏳ Ждем {PART_DELAY}с перед отправкой следующей части...")
            await asyncio.sleep(PART_DELAY)
    
    # Итоговая статистика
    if success_count == total:
        logger.info(f"[LONG MSG] ✅ Все {total} частей успешно отправлены в чат {chat_id}")
        return True
    else:
        logger.error(f"[LONG MSG] ❌ Отправлено только {success_count}/{total} частей в чат {chat_id}")
        return False


async def send_channel_message_with_retry(text: str, parse_mode: Optional[str] = None, 
                                        channel_id: str = None, token: str = None,
                                        disable_web_page_preview: bool = False):
    """
    Отправляет сообщение в канал с retry логикой.
    
    Args:
        text: Текст сообщения
        parse_mode: Режим парсинга
        channel_id: ID канала
        token: Токен бота
        disable_web_page_preview: Отключить превью ссылок
    
    Returns:
        bool: True если отправлено успешно
    """
    if not token or not channel_id:
        logger.error("❌ Токен бота или ID канала не предоставлены")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {
        "chat_id": channel_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview
    }
    if parse_mode:
        data["parse_mode"] = parse_mode

    for attempt in range(MAX_RETRIES):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info(f"✅ Сообщение отправлено в канал {channel_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка отправки в канал: {response.status} - {error_text}")
                        
                        # Обработка rate limiting
                        if response.status == 429:
                            wait_time = RETRY_DELAY * (2 ** attempt)
                            logger.warning(f"⏳ Rate limiting канала, ждем {wait_time}с (попытка {attempt + 1}/{MAX_RETRIES})")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        # Другие ошибки
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY)
                            continue
                        else:
                            return False
                            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке в канал (попытка {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                return False
    
    return False


async def send_long_channel_message_improved(text: str, parse_mode: Optional[str] = None,
                                           channel_id: str = None, token: str = None):
    """
    Улучшенная функция отправки длинных сообщений в канал.
    
    Args:
        text: Текст сообщения
        parse_mode: Режим парсинга
        channel_id: ID канала
        token: Токен бота
    
    Returns:
        bool: True если все части отправлены успешно
    """
    if not token or not channel_id:
        logger.error("❌ Токен бота или ID канала не предоставлены")
        return False
    
    # Разбиваем на части
    parts = []
    while text:
        if len(text) <= TELEGRAM_MSG_LIMIT:
            parts.append(text)
            break
        # Ищем ближайший разрыв строки до лимита
        split_idx = text.rfind('\n', 0, TELEGRAM_MSG_LIMIT)
        if split_idx == -1 or split_idx < TELEGRAM_MSG_LIMIT // 2:
            # Если нет нормального разрыва, режем по лимиту
            split_idx = TELEGRAM_MSG_LIMIT
        part = text[:split_idx].rstrip()
        parts.append(part)
        text = text[split_idx:].lstrip()
    
    total = len(parts)
    success_count = 0
    
    logger.info(f"[CHANNEL LONG MSG] Разбито на {total} частей")
    
    for idx, part in enumerate(parts, 1):
        logger.info(f"[CHANNEL LONG MSG] Отправка части {idx}/{total}, длина {len(part)} символов")
        
        # Retry логика для каждой части
        for retry_attempt in range(MAX_RETRIES):
            try:
                if await send_channel_message_with_retry(part, parse_mode, channel_id, token):
                    success_count += 1
                    logger.info(f"[CHANNEL LONG MSG] ✅ Часть {idx}/{total} успешно отправлена")
                    break
                else:
                    logger.error(f"[CHANNEL LONG MSG] ❌ Ошибка отправки части {idx} (попытка {retry_attempt + 1}/{MAX_RETRIES})")
                    if retry_attempt == MAX_RETRIES - 1:
                        logger.error(f"[CHANNEL LONG MSG] ❌ Часть {idx} не удалось отправить после всех попыток")
                        break
                    else:
                        await asyncio.sleep(RETRY_DELAY)
                        
            except Exception as e:
                logger.error(f"[CHANNEL LONG MSG] ❌ Исключение при отправке части {idx} (попытка {retry_attempt + 1}/{MAX_RETRIES}): {e}")
                if retry_attempt == MAX_RETRIES - 1:
                    logger.error(f"[CHANNEL LONG MSG] ❌ Часть {idx} не удалось отправить после всех попыток")
                    break
                else:
                    await asyncio.sleep(RETRY_DELAY)
        
        # Задержка между частями (кроме последней)
        if idx < total:
            logger.info(f"[CHANNEL LONG MSG] ⏳ Ждем {PART_DELAY}с перед отправкой следующей части...")
            await asyncio.sleep(PART_DELAY)
    
    # Итоговая статистика
    if success_count == total:
        logger.info(f"[CHANNEL LONG MSG] ✅ Все {total} частей успешно отправлены в канал {channel_id}")
        return True
    else:
        logger.error(f"[CHANNEL LONG MSG] ❌ Отправлено только {success_count}/{total} частей в канал {channel_id}")
        return False 