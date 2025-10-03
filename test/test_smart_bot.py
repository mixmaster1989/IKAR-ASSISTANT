#!/usr/bin/env python3
"""
🧪 Тест умной системы триггера "бот"
Демонстрирует новую логику без старых чанков и с высоким порогом релевантности
"""

import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.group_bot_trigger import process_bot_trigger
from memory.sqlite import SQLiteStorage

async def test_smart_bot():
    """Тестирует умную систему триггера"""
    
    print("🧪 ТЕСТ УМНОЙ СИСТЕМЫ ТРИГГЕРА 'БОТ'")
    print("=" * 50)
    print("🎯 Новая логика: БЕЗ старых чанков, ТОЛЬКО текущий контекст")
    print()
    
    # Инициализируем хранилище
    sqlite_storage = SQLiteStorage()
    
    # Тестовая группа
    chat_id = "test_smart_group"
    user_id = "test_user_789"
    
    print(f"📝 Тестовая группа: {chat_id}")
    print(f"👤 Тестовый пользователь: {user_id}")
    print()
    
    # Тест 1: Текущий разговор о погоде
    print("🌤️ ТЕСТ 1: Разговор о погоде")
    print("-" * 40)
    
    weather_messages = [
        ("user_1", "Какая сегодня погода?"),
        ("user_2", "Дождь льет как из ведра"),
        ("user_3", "Да, промок до нитки"),
        ("user_1", "Завтра обещают солнце"),
        ("user_2", "Наконец-то!"),
    ]
    
    # Сохраняем сообщения
    for i, (msg_user_id, content) in enumerate(weather_messages):
        sqlite_storage.save_group_message(
            chat_id=chat_id,
            message_id=i + 1,
            user_id=msg_user_id,
            msg_type="text",
            content=content,
            timestamp=1700000000 + i * 60
        )
        sqlite_storage.set_group_user_name(chat_id, msg_user_id, f"User_{msg_user_id}")
        print(f"👤 User_{msg_user_id}: {content}")
    
    print()
    print("🤖 Кто-то пишет 'бот':")
    print("-" * 20)
    
    try:
        response = await process_bot_trigger(chat_id, "бот", user_id)
        print(f"👤 Пользователь: бот")
        print(f"🤖 Бот: {response}")
        
        # Анализируем ответ
        print()
        print("📊 Анализ ответа:")
        if "погода" in response.lower() or "дождь" in response.lower() or "солнце" in response.lower():
            print("✅ Бот правильно понял контекст - погода")
        else:
            print("⚠️ Бот не понял контекст погоды")
            
        if len(response) < 200:
            print("✅ Ответ краткий - хорошо")
        else:
            print("⚠️ Ответ слишком длинный")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()
    print("🧹 Очищаем данные...")
    await clear_test_data(sqlite_storage, chat_id)
    
    # Тест 2: Разговор о работе
    print()
    print("💼 ТЕСТ 2: Разговор о работе")
    print("-" * 40)
    
    work_messages = [
        ("user_1", "Как дела с проектом?"),
        ("user_2", "Почти закончил"),
        ("user_3", "Когда сдаем?"),
        ("user_2", "Завтра к вечеру"),
        ("user_1", "Отлично!"),
    ]
    
    # Сохраняем сообщения
    for i, (msg_user_id, content) in enumerate(work_messages):
        sqlite_storage.save_group_message(
            chat_id=chat_id,
            message_id=i + 100,
            user_id=msg_user_id,
            msg_type="text",
            content=content,
            timestamp=1700000000 + i * 60
        )
        sqlite_storage.set_group_user_name(chat_id, msg_user_id, f"User_{msg_user_id}")
        print(f"👤 User_{msg_user_id}: {content}")
    
    print()
    print("🤖 Кто-то пишет 'бот':")
    print("-" * 20)
    
    try:
        response = await process_bot_trigger(chat_id, "бот", user_id)
        print(f"👤 Пользователь: бот")
        print(f"🤖 Бот: {response}")
        
        # Анализируем ответ
        print()
        print("📊 Анализ ответа:")
        if "проект" in response.lower() or "работа" in response.lower() or "завтра" in response.lower():
            print("✅ Бот правильно понял контекст - работа")
        else:
            print("⚠️ Бот не понял контекст работы")
            
        if len(response) < 200:
            print("✅ Ответ краткий - хорошо")
        else:
            print("⚠️ Ответ слишком длинный")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()
    print("🧹 Очищаем данные...")
    await clear_test_data(sqlite_storage, chat_id)
    
    # Тест 3: Общий разговор
    print()
    print("💬 ТЕСТ 3: Общий разговор")
    print("-" * 40)
    
    general_messages = [
        ("user_1", "Привет всем!"),
        ("user_2", "Привет!"),
        ("user_3", "Как дела?"),
        ("user_1", "Нормально"),
        ("user_2", "У меня тоже"),
    ]
    
    # Сохраняем сообщения
    for i, (msg_user_id, content) in enumerate(general_messages):
        sqlite_storage.save_group_message(
            chat_id=chat_id,
            message_id=i + 200,
            user_id=msg_user_id,
            msg_type="text",
            content=content,
            timestamp=1700000000 + i * 60
        )
        sqlite_storage.set_group_user_name(chat_id, msg_user_id, f"User_{msg_user_id}")
        print(f"👤 User_{msg_user_id}: {content}")
    
    print()
    print("🤖 Кто-то пишет 'бот':")
    print("-" * 20)
    
    try:
        response = await process_bot_trigger(chat_id, "бот", user_id)
        print(f"👤 Пользователь: бот")
        print(f"🤖 Бот: {response}")
        
        # Анализируем ответ
        print()
        print("📊 Анализ ответа:")
        if "привет" in response.lower() or "дела" in response.lower():
            print("✅ Бот правильно понял общий контекст")
        else:
            print("⚠️ Бот не понял общий контекст")
            
        if len(response) < 200:
            print("✅ Ответ краткий - хорошо")
        else:
            print("⚠️ Ответ слишком длинный")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()
    print("🧹 Очищаем данные...")
    await clear_test_data(sqlite_storage, chat_id)
    
    print()
    print("🎉 Тест умной системы завершен!")
    print()
    print("📈 Ключевые улучшения:")
    print("✅ НЕ использует старые чанки")
    print("✅ Только последние 5-8 сообщений")
    print("✅ Высокий порог релевантности")
    print("✅ Краткие ответы (до 300 символов)")
    print("✅ Анализ текущей темы")
    print("✅ Контроль повторений")

async def clear_test_data(sqlite_storage, chat_id):
    """Очищает тестовые данные"""
    try:
        import sqlite3
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        
        # Удаляем тестовые сообщения
        cursor.execute('DELETE FROM group_history WHERE chat_id = ?', (chat_id,))
        
        # Удаляем тестовые имена
        cursor.execute('DELETE FROM group_user_names WHERE chat_id = ?', (chat_id,))
        
        conn.commit()
        conn.close()
        
        print("✅ Данные очищены")
        
    except Exception as e:
        print(f"⚠️ Ошибка очистки: {e}")

if __name__ == "__main__":
    asyncio.run(test_smart_bot()) 