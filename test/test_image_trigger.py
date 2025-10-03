#!/usr/bin/env python3
"""
Тест для проверки работы группового триггера генерации изображений
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем backend в Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.api.group_image_trigger import GroupImageTrigger

async def mock_send_telegram_photo(chat_id: str, photo_path: str, caption: str = None):
    """Mock функция для тестирования отправки фотографий."""
    print(f"📸 MOCK: Отправка фото в чат {chat_id}")
    print(f"📁 Файл: {photo_path}")
    print(f"📝 Подпись: {caption}")
    
    # Проверяем, что файл существует
    if os.path.exists(photo_path):
        file_size = os.path.getsize(photo_path)
        print(f"✅ Файл найден, размер: {file_size} bytes")
        return True
    else:
        print(f"❌ Файл не найден: {photo_path}")
        return False

async def test_prompt_extraction():
    """Тест извлечения промпта из сообщения."""
    print("\n🧪 Тест извлечения промпта:")
    
    trigger = GroupImageTrigger()
    
    test_cases = [
        ("ботнарисуй кота на крыше", "кота на крыше"),
        ("БОТНАРИСУЙ красивый закат", "красивый закат"),
        ("Эй, ботнарисуй робота в космосе!", "робота в космосе"),
        ("ботнарисуй", ""),
        ("привет всем", ""),
        ("ботнарисуй картинку с драконом и замком", "картинку с драконом и замком"),
    ]
    
    for message, expected in test_cases:
        result = trigger._extract_prompt(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' → '{result}' (ожидалось: '{expected}')")

async def test_trigger_activation():
    """Тест активации триггера."""
    print("\n🧪 Тест активации триггера:")
    
    trigger = GroupImageTrigger()
    
    test_cases = [
        ("ботнарисуй кота", True),
        ("БОТНАРИСУЙ робота", True),
        ("Эй, ботнарисуй что-то", True),
        ("привет всем", False),
        ("говорим о ботах", False),
        ("ботнарисуй", True),  # Должен сработать, но показать инструкцию
    ]
    
    for message, should_trigger in test_cases:
        result = await trigger.try_trigger("test_chat", message, mock_send_telegram_photo)
        status = "✅" if result == should_trigger else "❌"
        print(f"{status} '{message}' → {result} (ожидалось: {should_trigger})")

async def test_cooldown():
    """Тест системы cooldown."""
    print("\n🧪 Тест системы cooldown:")
    
    trigger = GroupImageTrigger()
    trigger.cooldown_sec = 2  # Короткий cooldown для теста
    
    chat_id = "test_chat_cooldown"
            message = "картинка: тест"
    
    print("1. Первый запрос:")
    result1 = await trigger.try_trigger(chat_id, message, mock_send_telegram_photo)
    print(f"   Результат: {result1}")
    
    print("2. Второй запрос (должен быть заблокирован):")
    result2 = await trigger.try_trigger(chat_id, message, mock_send_telegram_photo)
    print(f"   Результат: {result2}")
    
    print("3. Ждем cooldown...")
    await asyncio.sleep(3)
    
    print("4. Третий запрос (должен пройти):")
    result3 = await trigger.try_trigger(chat_id, message, mock_send_telegram_photo)
    print(f"   Результат: {result3}")

async def test_instruction_message():
    """Тест отправки инструкций."""
    print("\n🧪 Тест отправки инструкций:")
    
    trigger = GroupImageTrigger()
    
    # Тест с пустым промптом
            result = await trigger.try_trigger("test_chat", "картинка:", mock_send_telegram_photo)
    print(f"Результат для пустого промпта: {result}")

async def main():
    """Основная функция тестирования."""
    print("🚀 Запуск тестов для группового триггера генерации изображений")
    print("=" * 60)
    
    try:
        await test_prompt_extraction()
        await test_trigger_activation()
        await test_cooldown()
        await test_instruction_message()
        
        print("\n" + "=" * 60)
        print("✅ Все тесты завершены!")
        print("\n📝 Для полного тестирования:")
        print("1. Убедитесь, что STABLE_HORDE_API_KEY настроен в .env")
        print("2. Перезапустите сервер: python run.py")
        print("3. Протестируйте в группе Telegram: 'картинка: кот'")
        
    except Exception as e:
        print(f"\n❌ Ошибка во время тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 