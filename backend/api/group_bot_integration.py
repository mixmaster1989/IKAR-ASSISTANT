#!/usr/bin/env python3
"""
🔗 Интеграция умного триггера "бот" в систему Telegram
Модуль для подключения нового умного триггера к основному polling
"""

import logging
from typing import Optional

logger = logging.getLogger("chatumba.group_bot_integration")

async def handle_bot_trigger_in_group(chat_id: str, message_text: str, user_id: str, 
                                     is_quote: bool = False, quoted_message_id: int = None, 
                                     is_mention: bool = False) -> bool:
    """
    Обрабатывает умный триггер "бот" в групповом чате (обычный, через цитирование или @username)
    
    Args:
        chat_id: ID чата
        message_text: Текст сообщения
        user_id: ID пользователя
        is_quote: Является ли это цитированием
        quoted_message_id: ID цитируемого сообщения
        is_mention: Является ли это упоминанием через @username
        
    Returns:
        bool: True если триггер сработал и был обработан
    """
    try:
        # Инициализируем интеграцию с памятью если нужно
        from .telegram_memory_integration import get_telegram_memory_integration
        integration = get_telegram_memory_integration()
        
        if not integration.initialized:
            await integration.initialize()
        
        # Обрабатываем умный триггер
        response = await integration.handle_smart_bot_trigger(chat_id, message_text, user_id, is_quote, quoted_message_id, is_mention)
        
        if response:
            # Проверяем, не является ли это специальным флагом подтверждения
            if response == "CONFIRMATION_SENT":
                logger.info(f"🔔 Кнопки подтверждения отправлены в чат {chat_id}")
                return True
            
            # Отправляем обычный ответ в группу и сохраняем диалог
            from .telegram_core import send_telegram_message
            message_id = await send_telegram_message(
                chat_id, 
                response, 
                save_dialogue=True, 
                user_message=message_text, 
                user_id=user_id
            )
            logger.info(f"🤖 Умный триггер 'бот' обработан в чате {chat_id} ({'цитирование' if is_quote else 'обычный'}) | ID: {message_id}")
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки умного триггера 'бот': {e}")
        return False

async def check_and_handle_bot_trigger(chat_id: str, message_text: str, user_id: str, 
                                      is_quote: bool = False, quoted_message_id: int = None, 
                                      is_mention: bool = False, group_names_mode: dict = None) -> bool:
    """
    Проверяет и обрабатывает умный триггер "бот" в любой группе (обычный, через цитирование или @username)
    
    Args:
        chat_id: ID чата
        message_text: Текст сообщения
        user_id: ID пользователя
        is_quote: Является ли это цитированием
        quoted_message_id: ID цитируемого сообщения
        is_mention: Является ли это упоминанием через @username
        group_names_mode: Словарь режимов групп (не используется)
        
    Returns:
        bool: True если триггер сработал и был обработан
    """
    # Умный триггер "бот" работает везде, где бот добавлен
    # Автоматически сохраняет сообщения в память и использует умный контекст
    
    # Обрабатываем триггер
    return await handle_bot_trigger_in_group(chat_id, message_text, user_id, is_quote, quoted_message_id, is_mention)

async def handle_memory_export_trigger_in_group(chat_id: str, message_text: str, user_id: str) -> bool:
    """
    Обрабатывает триггер экспорта памяти "ПАМЯТЬ" в групповом чате
    
    Args:
        chat_id: ID чата
        message_text: Текст сообщения
        user_id: ID пользователя
        
    Returns:
        bool: True если триггер сработал и был обработан
    """
    try:
        # Импортируем триггер экспорта памяти
        from .memory_export_trigger import process_memory_export_trigger
        
        # Обрабатываем триггер экспорта памяти
        response = await process_memory_export_trigger(chat_id, message_text, user_id)
        
        if response:
            # Проверяем, не является ли это специальным флагом подтверждения
            if response == "CONFIRMATION_SENT":
                logger.info(f"🔔 Кнопки подтверждения отправлены в чат {chat_id}")
                return True
            
            # Отправляем обычный ответ в группу и сохраняем диалог
            # Отправляем ответ в группу
            from .telegram_core import send_telegram_message
            message_id = await send_telegram_message(chat_id, response)
            logger.info(f"📁 Триггер экспорта памяти 'ПАМЯТЬ' обработан в чате {chat_id} | ID: {message_id}")
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки триггера экспорта памяти 'ПАМЯТЬ': {e}")
        return False

async def check_and_handle_memory_export_trigger(chat_id: str, message_text: str, user_id: str) -> bool:
    """
    Проверяет и обрабатывает триггер экспорта памяти "ПАМЯТЬ" в любой группе
    
    Args:
        chat_id: ID чата
        message_text: Текст сообщения
        user_id: ID пользователя
        
    Returns:
        bool: True если триггер сработал и был обработан
    """
    # Триггер экспорта памяти работает везде, где бот добавлен
    # Создает текстовый файл со всеми чанками памяти группы
    
    # Обрабатываем триггер
    return await handle_memory_export_trigger_in_group(chat_id, message_text, user_id) 