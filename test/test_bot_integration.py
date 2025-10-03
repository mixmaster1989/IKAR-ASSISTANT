#!/usr/bin/env python3
"""
🧪 Тест интеграции триггера "бот" в систему Telegram
"""

import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.group_bot_integration import check_and_handle_bot_trigger

async def test_bot_integration():
    """Тестирует интеграцию триггера 'бот'"""
    
    print("🧪 ТЕСТ ИНТЕГРАЦИИ ТРИГГЕРА 'БОТ'")
    print("=" * 50)
    
    # Тестовые данные
    chat_id = "test_group_123"
    user_id = "test_user_456"
    
    # Тестовые сообщения
    test_cases = [
        ("бот", True, "Точное слово 'бот'"),
        ("БОТ", True, "Точное слово 'БОТ' (заглавные)"),
        ("Привет, бот!", True, "Слово 'бот' в предложении"),
        ("работает", False, "Часть слова 'работает'"),
        ("робот", False, "Часть слова 'робот'"),
        ("привет", False, "Обычное сообщение"),
    ]
    
    print("📋 Тестируем интеграцию:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for message, expected_trigger, description in test_cases:
        try:
            result = await check_and_handle_bot_trigger(chat_id, message, user_id)
            status = "✅ ПРОШЕЛ" if result == expected_trigger else "❌ ПРОВАЛ"
            
            print(f"{status} | '{message}' | {description}")
            print(f"   Ожидалось: {expected_trigger}, Получено: {result}")
            
            if result == expected_trigger:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ ОШИБКА | '{message}' | {description}")
            print(f"   Ошибка: {e}")
            failed += 1
    
    print("-" * 50)
    print(f"📊 РЕЗУЛЬТАТ: {passed} прошло, {failed} провалилось")
    
    # Тест с разными группами
    print("\n🔒 Тест с разными группами:")
    print("-" * 30)
    
    # Тест в другой группе
    other_chat_id = "test_group_456"
    result = await check_and_handle_bot_trigger(other_chat_id, "бот", user_id)
    print(f"Другая группа + 'бот': {result} (должно быть True)")
    
    print("\n🎉 Тест интеграции завершен!")

if __name__ == "__main__":
    asyncio.run(test_bot_integration()) 