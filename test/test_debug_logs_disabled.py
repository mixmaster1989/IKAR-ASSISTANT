#!/usr/bin/env python3
"""
🧪 ТЕСТ ОТКЛЮЧЕНИЯ DEBUG ЛОГОВ
Проверяем, что debug логи от сторонних библиотек отключены
"""

import logging
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

def test_debug_logs_disabled():
    """Тест отключения debug логов"""
    print("🧪 ТЕСТ ОТКЛЮЧЕНИЯ DEBUG ЛОГОВ")
    print("=" * 50)
    
    # Проверяем уровни логирования для сторонних библиотек
    third_party_loggers = [
        'htmldate', 'trafilatura', 'newspaper', 'readability', 'justext',
        'bs4', 'urllib3', 'aiohttp', 'asyncio', 'charset_normalizer',
        'requests', 'feedparser', 'nltk', 'lxml', 'html5lib'
    ]
    
    print("📋 Проверяем уровни логирования:")
    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        level_name = logging.getLevelName(logger.level)
        status = "✅ ОТКЛЮЧЕН" if logger.level >= logging.WARNING else "❌ ВКЛЮЧЕН"
        print(f"   {logger_name:20} -> {level_name:8} {status}")
    
    # Тестируем функцию отключения
    print("\n🔧 Тестируем функцию отключения:")
    try:
        from internet_intelligence_logger import disable_third_party_debug_logs
        disable_third_party_debug_logs()
        print("✅ Функция disable_third_party_debug_logs() работает")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
    
    # Проверяем снова после вызова функции
    print("\n📋 Проверяем уровни после вызова функции:")
    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        level_name = logging.getLevelName(logger.level)
        status = "✅ ОТКЛЮЧЕН" if logger.level >= logging.WARNING else "❌ ВКЛЮЧЕН"
        print(f"   {logger_name:20} -> {level_name:8} {status}")
    
    print("\n🎯 РЕЗУЛЬТАТ:")
    all_disabled = all(
        logging.getLogger(name).level >= logging.WARNING 
        for name in third_party_loggers
    )
    
    if all_disabled:
        print("✅ ВСЕ DEBUG ЛОГИ ОТКЛЮЧЕНЫ!")
        print("   Теперь в консоли не будет лишних debug сообщений от библиотек парсинга")
    else:
        print("❌ НЕКОТОРЫЕ DEBUG ЛОГИ ВСЕ ЕЩЕ ВКЛЮЧЕНЫ")
        print("   Нужно проверить настройки логирования")

if __name__ == "__main__":
    test_debug_logs_disabled() 