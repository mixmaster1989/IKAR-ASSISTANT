#!/usr/bin/env python3
"""
Скрипт для инициализации Smart Context Preloader существующими данными
"""

import sys
import os
import sqlite3
import time
from datetime import datetime, timedelta

# Добавляем backend в путь
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from memory.smart_context_preloader import SmartContextPreloader

def init_preloader_with_existing_data():
    """Инициализирует прелоадер существующими данными из базы"""
    
    print("🚀 Инициализация Smart Context Preloader существующими данными")
    print("=" * 60)
    
    # Подключаемся к базе данных
    db_path = "data/chatumba.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем все сообщения, сгруппированные по пользователю
    cursor.execute("""
        SELECT user_id, role, message, timestamp 
        FROM chat_history 
        ORDER BY user_id, timestamp
    """)
    
    messages = cursor.fetchall()
    conn.close()
    
    if not messages:
        print("❌ Сообщений в базе данных не найдено")
        return
    
    print(f"📊 Найдено {len(messages)} сообщений в базе данных")
    
    # Группируем сообщения по пользователям
    user_messages = {}
    for user_id, role, message, timestamp in messages:
        if user_id not in user_messages:
            user_messages[user_id] = []
        user_messages[user_id].append({
            'role': role,
            'message': message,
            'timestamp': timestamp
        })
    
    print(f"👥 Найдено {len(user_messages)} пользователей")
    
    # Инициализируем прелоадер
    preloader = SmartContextPreloader(db_path)
    
    # Обрабатываем каждого пользователя
    for user_id, user_msgs in user_messages.items():
        print(f"\n👤 Обрабатываем пользователя: {user_id}")
        
        # Извлекаем chat_id из user_id (убираем префикс tg_)
        chat_id = user_id.replace("tg_", "")
        
        # Сортируем сообщения по времени
        user_msgs.sort(key=lambda x: x['timestamp'])
        
        # Отслеживаем только сообщения пользователя (не ассистента)
        user_only_messages = [msg for msg in user_msgs if msg['role'] == 'user']
        
        if not user_only_messages:
            print(f"   ⚠️  Нет сообщений от пользователя")
            continue
        
        print(f"   📝 Сообщений от пользователя: {len(user_only_messages)}")
        
        # Отслеживаем каждое сообщение пользователя
        for i, msg in enumerate(user_only_messages):
            # Вычисляем примерное время ответа (время до следующего сообщения ассистента)
            response_time = 2.0  # базовое время
            
            if i < len(user_only_messages) - 1:
                next_msg_time = user_only_messages[i + 1]['timestamp']
                response_time = next_msg_time - msg['timestamp']
                response_time = max(0.5, min(response_time, 30.0))  # ограничиваем разумными пределами
            
            # Отслеживаем сообщение
            preloader.track_message(user_id, chat_id, msg['message'], response_time)
            
            # Небольшая задержка для имитации реального времени
            time.sleep(0.01)
        
        print(f"   ✅ Обработано {len(user_only_messages)} сообщений")
    
    # Запускаем прелоадер
    print(f"\n🚀 Запускаем Smart Context Preloader...")
    preloader.start()
    
    # Ждем немного для создания контекстов
    print("⏳ Ждем создания контекстов...")
    time.sleep(10)
    
    # Получаем статистику
    stats = preloader.get_stats()
    print(f"\n📊 Финальная статистика:")
    print(f"   Активных пользователей: {stats['active_users']}")
    print(f"   Кэшированных контекстов: {stats['cached_contexts']}")
    print(f"   Использование памяти: {stats['memory_usage']['total_kb']} KB")
    
    # Показываем активных пользователей
    if preloader.user_activities:
        print(f"\n👥 Активные пользователи:")
        for key, activity in preloader.user_activities.items():
            print(f"   {key}: {activity.message_count} сообщений, "
                  f"последняя активность: {datetime.fromtimestamp(activity.last_message_time).strftime('%H:%M:%S')}")
    
    print(f"\n✅ Инициализация завершена!")
    print(f"🌐 Проверьте статус в веб-интерфейсе: https://igorhook6666.loca.lt/context-preloader.html")
    
    return preloader

if __name__ == "__main__":
    init_preloader_with_existing_data() 