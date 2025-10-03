#!/usr/bin/env python3
"""
Тест для проверки отключения DEBUG логов от внешних библиотек
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from utils.logger import setup_logging
import logging

def test_logging_setup():
    """Тестирует настройку логирования"""
    print("🔧 Настройка логирования...")
    setup_logging()
    
    print("\n📋 Проверка уровней логирования:")
    
    # Проверяем наши логгеры
    our_loggers = [
        'chatumba.telegram',
        'chatumba.personality',
        'chatumba.embeddings'
    ]
    
    for logger_name in our_loggers:
        logger = logging.getLogger(logger_name)
        print(f"  {logger_name}: {logger.level} ({logging.getLevelName(logger.level)})")
    
    # Проверяем внешние логгеры
    external_loggers = [
        'urllib3',
        'urllib3.connectionpool',
        'sentence_transformers',
        'sentence_transformers.SentenceTransformer',
        'transformers',
        'huggingface_hub'
    ]
    
    print("\n🚫 Внешние логгеры (должны быть WARNING или выше):")
    for logger_name in external_loggers:
        logger = logging.getLogger(logger_name)
        print(f"  {logger_name}: {logger.level} ({logging.getLevelName(logger.level)})")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    test_logging_setup() 