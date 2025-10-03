#!/usr/bin/env python3
"""
🧪 Тест группового триггера "бот"
Проверка точного распознавания слова "бот"
"""

import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.group_bot_trigger import GroupBotTrigger

async def test_bot_trigger():
    """Тестирует работу триггера 'бот'"""
    
    print("🧪 ТЕСТ ТРИГГЕРА 'БОТ'")
    print("=" * 50)
    
    # Создаем экземпляр триггера
    trigger = GroupBotTrigger()
    
    # Тестовые сообщения
    test_messages = [
        # Должны сработать (точное слово "бот")
        ("бот", True, "Точное слово 'бот'"),
        ("БОТ", True, "Точное слово 'БОТ' (заглавные)"),
        ("Бот", True, "Точное слово 'Бот' (с заглавной)"),
        ("Привет, бот!", True, "Слово 'бот' в предложении"),
        ("бот, как дела?", True, "Слово 'бот' в начале"),
        ("Как дела, бот?", True, "Слово 'бот' в конце"),
        ("Это бот.", True, "Слово 'бот' с точкой"),
        ("бот,", True, "Слово 'бот' с запятой"),
        ("бот!", True, "Слово 'бот' с восклицательным знаком"),
        
        # НЕ должны сработать (части других слов)
        ("работает", False, "Часть слова 'работает'"),
        ("робот", False, "Часть слова 'робот'"),
        ("ботовод", False, "Часть слова 'ботовод'"),
        ("ботокс", False, "Часть слова 'ботокс'"),
        ("ботва", False, "Часть слова 'ботва'"),
        ("боты", False, "Множественное число 'боты'"),
        ("бота", False, "Родительный падеж 'бота'"),
        ("боту", False, "Дательный падеж 'боту'"),
        ("ботом", False, "Творительный падеж 'ботом'"),
        ("боте", False, "Предложный падеж 'боте'"),
        
        # Пустые и специальные случаи
        ("", False, "Пустое сообщение"),
        ("привет", False, "Обычное сообщение без 'бот'"),
        ("123", False, "Только цифры"),
        ("!@#$%", False, "Только символы"),
    ]
    
    print("📋 Тестируем распознавание слова 'бот':")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for message, expected, description in test_messages:
        result = trigger.is_triggered(message)
        status = "✅ ПРОШЕЛ" if result == expected else "❌ ПРОВАЛ"
        
        print(f"{status} | '{message}' | {description}")
        print(f"   Ожидалось: {expected}, Получено: {result}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"📊 РЕЗУЛЬТАТ: {passed} прошло, {failed} провалилось")
    
    # Тест cooldown
    print("\n⏰ Тестируем cooldown:")
    print("-" * 30)
    
    chat_id = "test_chat_123"
    
    # Первый вызов - должен сработать
    result1 = await trigger.process_trigger(chat_id, "бот", "user1")
    print(f"Первый вызов: {result1}")
    
    # Второй вызов сразу - должен быть cooldown
    result2 = await trigger.process_trigger(chat_id, "бот", "user2")
    print(f"Второй вызов (cooldown): {result2}")
    
    # Тест статистики
    print("\n📈 Статистика триггера:")
    print("-" * 30)
    stats = trigger.get_stats()
    print(f"Активных чатов: {stats['active_chats']}")
    print(f"Cooldown (сек): {stats['cooldown_seconds']}")
    print(f"Последние триггеры: {stats['last_triggers']}")
    
    print("\n🎉 Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_bot_trigger()) 