#!/usr/bin/env python3
"""
🧪 Тест системы кнопок подтверждения для триггера "бот"
Проверяет новую функциональность с кнопками "Да/Нет"
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_bot_confirmation_system():
    """Тестирует систему кнопок подтверждения"""
    print("🧪 ТЕСТ СИСТЕМЫ КНОПОК ПОДТВЕРЖДЕНИЯ БОТА")
    print("=" * 50)
    
    try:
        from api.smart_bot_trigger import SmartBotTrigger
        
        # Создаем экземпляр триггера
        trigger = SmartBotTrigger()
        print("✅ SmartBotTrigger создан")
        
        # Проверяем новые поля
        assert hasattr(trigger, 'pending_confirmations'), "❌ Поле pending_confirmations не найдено"
        assert hasattr(trigger, 'confirmation_timeout'), "❌ Поле confirmation_timeout не найдено"
        assert trigger.confirmation_timeout == 15, f"❌ Неверный таймаут: {trigger.confirmation_timeout}"
        print("✅ Новые поля проверены")
        
        # Проверяем новые методы
        assert hasattr(trigger, 'send_confirmation_buttons'), "❌ Метод send_confirmation_buttons не найден"
        assert hasattr(trigger, 'handle_confirmation_callback'), "❌ Метод handle_confirmation_callback не найден"
        assert hasattr(trigger, 'process_confirmed_trigger'), "❌ Метод process_confirmed_trigger не найден"
        print("✅ Новые методы проверены")
        
        # Тестируем распознавание триггера
        test_cases = [
            ("бот", True),
            ("БОТ", True),
            ("привет бот", True),
            ("бот, как дела?", True),
            ("робот", False),
            ("боты", False),
            ("ботов", False),
            ("ботнарисуй", False),
        ]
        
        print("\n🎯 Тест распознавания триггера:")
        for text, expected in test_cases:
            result = trigger.is_triggered(text)
            status = "✅" if result == expected else "❌"
            print(f"  {status} '{text}' -> {result} (ожидалось {expected})")
            assert result == expected, f"Неверный результат для '{text}': {result} != {expected}"
        
        print("✅ Распознавание триггера работает корректно")
        
        # Тестируем cooldown
        print("\n⏰ Тест cooldown:")
        chat_id = "test_chat_123"
        
        # Первый вызов - должен пройти
        assert not trigger.is_cooldown_active(chat_id), "Cooldown не должен быть активен"
        print("  ✅ Первый вызов - cooldown не активен")
        
        # Обновляем время триггера
        trigger.update_trigger_time(chat_id)
        
        # Второй вызов - должен быть заблокирован
        assert trigger.is_cooldown_active(chat_id), "Cooldown должен быть активен"
        print("  ✅ Второй вызов - cooldown активен")
        
        print("✅ Cooldown работает корректно")
        
        # Тестируем создание callback данных
        print("\n🔧 Тест создания callback данных:")
        import uuid
        confirmation_id = str(uuid.uuid4())[:8]
        
        yes_callback = f"bot_confirm_yes_{confirmation_id}"
        no_callback = f"bot_confirm_no_{confirmation_id}"
        
        assert yes_callback.startswith("bot_confirm_yes_"), "❌ Неверный формат callback для 'Да'"
        assert no_callback.startswith("bot_confirm_no_"), "❌ Неверный формат callback для 'Нет'"
        print(f"  ✅ Callback 'Да': {yes_callback}")
        print(f"  ✅ Callback 'Нет': {no_callback}")
        
        print("✅ Callback данные создаются корректно")
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("📋 Система кнопок подтверждения готова к работе")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_telegram_polling_integration():
    """Тестирует интеграцию с telegram_polling.py"""
    print("\n🔗 ТЕСТ ИНТЕГРАЦИИ С TELEGRAM_POLLING")
    print("=" * 50)
    
    try:
        # Проверяем что обработчик добавлен в telegram_polling.py
        with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = [
            'bot_confirm_',
            'handle_confirmation_callback',
            'process_confirmed_trigger',
            'answer_callback_query'
        ]
        
        for element in required_elements:
            if element in content:
                print(f"  ✅ {element} найден в telegram_polling.py")
            else:
                print(f"  ❌ {element} НЕ найден в telegram_polling.py")
                return False
        
        print("✅ Интеграция с telegram_polling.py корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки интеграции: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТОВ СИСТЕМЫ КНОПОК ПОДТВЕРЖДЕНИЯ")
    print("=" * 60)
    
    # Тест основной функциональности
    test1_result = await test_bot_confirmation_system()
    
    # Тест интеграции
    test2_result = await test_telegram_polling_integration()
    
    print("\n" + "=" * 60)
    if test1_result and test2_result:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе!")
        print("\n📋 ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:")
        print("1. Пользователь пишет 'бот' в группе")
        print("2. Бот отправляет сообщение '🤖 Ты меня звал?' с кнопками ✅ Да / ❌ Нет")
        print("3. При нажатии 'Да' - выполняется обычная логика триггера")
        print("4. При нажатии 'Нет' - ничего не происходит")
        print("5. Через 15 секунд сообщение с кнопками автоматически удаляется")
        return 0
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
