#!/usr/bin/env python3
"""
🧪 Тест контекстной работы триггера "бот"
Демонстрирует, как бот получает контекст из группы и отвечает уместно
"""

import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.group_bot_trigger import process_bot_trigger
from memory.sqlite import SQLiteStorage

async def test_bot_context():
    """Тестирует работу триггера с контекстом группы"""
    
    print("🧪 ТЕСТ КОНТЕКСТНОЙ РАБОТЫ ТРИГГЕРА 'БОТ'")
    print("=" * 50)
    
    # Инициализируем хранилище
    sqlite_storage = SQLiteStorage()
    
    # Тестовая группа
    chat_id = "test_group_context"
    user_id = "test_user_456"
    
    print(f"📝 Тестовая группа: {chat_id}")
    print(f"👤 Тестовый пользователь: {user_id}")
    print()
    
    # Симулируем контекст разговора
    print("💬 Симулируем контекст разговора в группе:")
    print("-" * 40)
    
    # Сообщения для контекста
    context_messages = [
        ("user_1", "Привет всем! Как дела?"),
        ("user_2", "Привет! Все хорошо, работаю над проектом"),
        ("user_1", "Какой проект?"),
        ("user_2", "Делаю бота для Telegram, но что-то не получается"),
        ("user_3", "А что именно не работает?"),
        ("user_2", "Не могу понять, почему не отправляются сообщения"),
        ("user_1", "Может, проблема в токене?"),
        ("user_2", "Токен проверил, все правильно"),
        ("user_3", "Покажи код, может найдем ошибку"),
        ("user_2", "Хорошо, сейчас покажу"),
    ]
    
    # Сохраняем сообщения в базу
    for i, (msg_user_id, content) in enumerate(context_messages):
        sqlite_storage.save_group_message(
            chat_id=chat_id,
            message_id=i + 1,
            user_id=msg_user_id,
            msg_type="text",
            content=content,
            timestamp=1700000000 + i * 60  # Каждое сообщение через минуту
        )
        
        # Сохраняем имена пользователей
        sqlite_storage.set_group_user_name(chat_id, msg_user_id, f"User_{msg_user_id}")
        
        print(f"👤 User_{msg_user_id}: {content}")
    
    print()
    print("🤖 Теперь кто-то пишет 'бот':")
    print("-" * 40)
    
    # Тестируем триггер с контекстом
    try:
        response = await process_bot_trigger(chat_id, "бот", user_id)
        
        print(f"👤 Пользователь: бот")
        print(f"🤖 Бот: {response}")
        
        print()
        print("✅ Тест контекстной работы завершен!")
        print()
        print("📊 Анализ ответа:")
        print("-" * 20)
        
        # Анализируем ответ
        if "код" in response.lower() or "проект" in response.lower() or "бот" in response.lower():
            print("✅ Бот правильно понял контекст - обсуждается разработка бота")
        else:
            print("⚠️ Бот не полностью понял контекст")
            
        if "помочь" in response.lower() or "поможем" in response.lower():
            print("✅ Бот предложил помощь - это хорошо")
        else:
            print("⚠️ Бот не предложил помощь")
            
        if "🤖" in response or "💻" in response or "🔧" in response:
            print("✅ Бот использовал эмодзи - стиль общения хороший")
        else:
            print("⚠️ Бот не использовал эмодзи")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
    
    print()
    print("🧹 Очищаем тестовые данные...")
    
    # Очищаем тестовые данные
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
        
        print("✅ Тестовые данные очищены")
        
    except Exception as e:
        print(f"⚠️ Ошибка очистки данных: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_context()) 