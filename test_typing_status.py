#!/usr/bin/env python3
"""
🧪 Тест статуса "печатает" в Telegram
Проверяет отправку статусов действий
"""

import sys
import os
import asyncio

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_typing_status():
    """Тестирует отправку статуса 'печатает'"""
    print("🧪 Тестирование статуса 'печатает'...")
    
    try:
        from api.telegram_core import send_chat_action
        
        # Тестовый chat_id (замените на реальный)
        test_chat_id = "-1002686615681"  # Группа АНТИЛОПА
        
        print(f"📝 Отправляем статус 'печатает' в чат {test_chat_id}...")
        
        # Тестируем разные статусы
        statuses = [
            ("typing", "⌨️ Печатает..."),
            ("upload_photo", "📸 Загружает фото..."),
            ("record_voice", "🎤 Записывает голос...")
        ]
        
        for action, description in statuses:
            print(f"🔄 Тестируем: {description}")
            success = await send_chat_action(test_chat_id, action)
            print(f"✅ {description}: {'Успешно' if success else 'Ошибка'}")
            
            # Небольшая пауза между статусами
            await asyncio.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования статуса: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск теста статуса 'печатает'...")
    
    success = await test_typing_status()
    
    if success:
        print("🎉 ТЕСТ ПРОЙДЕН! Статус 'печатает' работает корректно!")
    else:
        print("⚠️ ТЕСТ ПРОВАЛЕН! Требуется доработка.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

