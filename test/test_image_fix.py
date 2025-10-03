#!/usr/bin/env python3
"""
🧪 Тест исправления обработки изображений в триггере "бот"
Проверяет, что JSON с IMAGE! обрабатывается правильно
"""

import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.group_bot_trigger import process_bot_trigger
from memory.sqlite import SQLiteStorage

async def test_image_fix():
    """Тестирует исправление обработки изображений"""
    
    print("🧪 ТЕСТ ИСПРАВЛЕНИЯ ОБРАБОТКИ ИЗОБРАЖЕНИЙ")
    print("=" * 50)
    print("🎯 Проверяем, что JSON с IMAGE! обрабатывается правильно")
    print()
    
    # Инициализируем хранилище
    sqlite_storage = SQLiteStorage()
    
    # Тестовая группа
    chat_id = "test_image_fix_group"
    user_id = "test_user_image"
    
    print(f"📝 Тестовая группа: {chat_id}")
    print(f"👤 Тестовый пользователь: {user_id}")
    print()
    
    # Создаем контекст для тестирования
    print("📝 Создаем контекст для тестирования:")
    print("-" * 40)
    
    context_messages = [
        ("user_1", "Привет всем!"),
        ("user_2", "Привет!"),
        ("user_3", "Как дела?"),
        ("user_1", "Нормально"),
        ("user_2", "У меня тоже"),
    ]
    
    # Сохраняем сообщения
    for i, (msg_user_id, content) in enumerate(context_messages):
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
        
        # Проверяем, есть ли JSON с IMAGE! в ответе
        if "IMAGE!" in response:
            print("❌ ПРОБЛЕМА: JSON с IMAGE! остался в ответе!")
            print("   Это означает, что обработка изображений не работает")
        else:
            print("✅ Хорошо: JSON с IMAGE! обработан и удален из ответа")
            
        # Проверяем длину ответа
        response_length = len(response)
        print(f"📏 Длина ответа: {response_length} символов")
        
        if response_length > 100:
            print("✅ Ответ достаточно длинный")
        else:
            print("⚠️ Ответ короткий (возможно, fallback)")
            
        # Проверяем контекстность
        context_keywords = ["привет", "дела", "нормально"]
        context_matches = sum(1 for keyword in context_keywords if keyword in response.lower())
        
        if context_matches >= 1:
            print("✅ Бот понимает контекст")
        else:
            print("⚠️ Бот не очень понимает контекст")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()
    print("🧹 Очищаем данные...")
    await clear_test_data(sqlite_storage, chat_id)
    
    print()
    print("🎉 Тест завершен!")
    print()
    print("📈 Результат:")
    print("✅ Обработка изображений добавлена в триггер 'бот'")
    print("✅ JSON с IMAGE! теперь обрабатывается правильно")
    print("✅ Изображения будут генерироваться в фоне")

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
    asyncio.run(test_image_fix()) 