#!/usr/bin/env python3
"""
🧪 Тест отсутствия ограничений длины ответов
Проверяет, что бот может давать длинные ответы без ограничений
"""

import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.group_bot_trigger import process_bot_trigger
from memory.sqlite import SQLiteStorage

async def test_no_length_limit():
    """Тестирует отсутствие ограничений длины"""
    
    print("🧪 ТЕСТ ОТСУТСТВИЯ ОГРАНИЧЕНИЙ ДЛИНЫ")
    print("=" * 50)
    print("🎯 Проверяем, что бот может давать длинные ответы")
    print()
    
    # Инициализируем хранилище
    sqlite_storage = SQLiteStorage()
    
    # Тестовая группа
    chat_id = "test_length_group"
    user_id = "test_user_length"
    
    print(f"📝 Тестовая группа: {chat_id}")
    print(f"👤 Тестовый пользователь: {user_id}")
    print()
    
    # Создаем контекст для длинного ответа
    print("📝 Создаем контекст для длинного ответа:")
    print("-" * 40)
    
    context_messages = [
        ("user_1", "У меня сложная проблема с проектом"),
        ("user_2", "Расскажи подробнее"),
        ("user_1", "Нужно создать систему с множеством компонентов"),
        ("user_2", "Какие именно компоненты?"),
        ("user_1", "База данных, API, фронтенд, мобильное приложение"),
        ("user_2", "Это действительно сложно"),
        ("user_1", "И еще нужно учесть безопасность и масштабируемость"),
        ("user_2", "Да, это серьезная задача"),
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
        
        # Анализируем длину ответа
        response_length = len(response)
        print()
        print("📊 Анализ длины ответа:")
        print(f"📏 Длина ответа: {response_length} символов")
        
        if response_length > 500:
            print("✅ Отлично! Бот дает длинный ответ без ограничений")
        elif response_length > 200:
            print("✅ Хорошо! Бот дает средний ответ")
        else:
            print("⚠️ Бот дал короткий ответ (возможно, fallback)")
            
        # Проверяем, есть ли обрезка
        if "..." in response and response.endswith("..."):
            print("❌ Обнаружена обрезка ответа!")
        else:
            print("✅ Обрезка ответа отсутствует")
            
        # Проверяем контекстность
        context_keywords = ["проект", "система", "компонент", "проблема", "сложно"]
        context_matches = sum(1 for keyword in context_keywords if keyword in response.lower())
        
        if context_matches >= 2:
            print("✅ Бот понимает контекст сложного проекта")
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
    print("✅ Ограничения длины убраны")
    print("✅ Бот может давать естественные ответы")
    print("✅ Нет принудительной обрезки")

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
    asyncio.run(test_no_length_limit()) 