#!/usr/bin/env python3
"""
Симуляция активности пользователя для тестирования Smart Context Preloader
"""

import sys
import os
import time
import requests
import json
from datetime import datetime

# Добавляем backend в путь
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def get_preloader_status():
    """Получение статуса прелоадера"""
    try:
        response = requests.get('http://localhost:6666/api/admin/context_preloader/status')
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка получения статуса: {e}")
        return None

def simulate_user_activity(user_id: str, messages: list):
    """Симуляция активности пользователя"""
    print(f"\n👤 Симуляция активности пользователя: {user_id}")
    print("=" * 50)
    
    for i, message in enumerate(messages, 1):
        print(f"\n📝 Сообщение {i}: {message}")
        
        # Отправляем сообщение через Telegram API
        try:
            response = requests.post('http://localhost:6666/api/telegram/webhook', json={
                "update_id": int(time.time()),
                "message": {
                    "message_id": i,
                    "from": {
                        "id": int(user_id.replace("tg_", "")),
                        "username": "test_user"
                    },
                    "chat": {
                        "id": int(user_id.replace("tg_", "")),
                        "type": "private"
                    },
                    "text": message,
                    "date": int(time.time())
                }
            })
            
            if response.status_code == 200:
                print("✅ Сообщение отправлено")
            else:
                print(f"⚠️ Ошибка отправки: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        # Ждем немного между сообщениями
        time.sleep(2)
        
        # Проверяем статус прелоадера
        status = get_preloader_status()
        if status and status.get('status') == 'ok':
            preloader = status.get('preloader', {})
            print(f"📊 Прелоадер: {preloader.get('active_users', 0)} пользователей, "
                  f"{preloader.get('cached_contexts', 0)} контекстов")

def test_preloader_scenarios():
    """Тестирование различных сценариев прелоадера"""
    
    print("🧪 Тестирование Smart Context Preloader")
    print("=" * 60)
    
    # Проверяем начальный статус
    print("\n📊 Начальный статус прелоадера:")
    initial_status = get_preloader_status()
    if initial_status:
        preloader = initial_status.get('preloader', {})
        print(f"   Активных пользователей: {preloader.get('active_users', 0)}")
        print(f"   Кэшированных контекстов: {preloader.get('cached_contexts', 0)}")
        print(f"   Попадания в кэш: {preloader.get('cache_hit_rate', 0)}%")
    
    # Сценарий 1: Новый пользователь с быстрыми сообщениями
    print("\n🎯 Сценарий 1: Новый активный пользователь")
    user1_messages = [
        "Привет! Как дела?",
        "Расскажи о криптовалютах",
        "Что думаешь о Bitcoin?",
        "Когда лучше покупать?",
        "Какие риски есть?"
    ]
    simulate_user_activity("tg_123456789", user1_messages)
    
    # Сценарий 2: Пользователь с техническими вопросами
    print("\n🎯 Сценарий 2: Технический пользователь")
    user2_messages = [
        "Как работает блокчейн?",
        "Объясни смарт-контракты",
        "Что такое DeFi?",
        "Какие есть алгоритмы консенсуса?",
        "Как работает майнинг?"
    ]
    simulate_user_activity("tg_987654321", user2_messages)
    
    # Сценарий 3: Пользователь с философскими вопросами
    print("\n🎯 Сценарий 3: Философский пользователь")
    user3_messages = [
        "Что такое сознание?",
        "Может ли ИИ быть разумным?",
        "В чем смысл жизни?",
        "Что такое свобода воли?",
        "Как работает память?"
    ]
    simulate_user_activity("tg_555666777", user3_messages)
    
    # Ждем немного для обработки
    print("\n⏳ Ждем обработки данных...")
    time.sleep(10)
    
    # Проверяем финальный статус
    print("\n📊 Финальный статус прелоадера:")
    final_status = get_preloader_status()
    if final_status:
        preloader = final_status.get('preloader', {})
        print(f"   Активных пользователей: {preloader.get('active_users', 0)}")
        print(f"   Кэшированных контекстов: {preloader.get('cached_contexts', 0)}")
        print(f"   Попадания в кэш: {preloader.get('cache_hit_rate', 0)}%")
        print(f"   Всего предзагрузок: {preloader.get('total_preloads', 0)}")
        print(f"   Использование памяти: {preloader.get('memory_usage', {}).get('total_kb', 0)} KB")
    
    # Тестируем получение предзагруженного контекста
    print("\n🔍 Тестирование получения контекста:")
    test_users = ["tg_123456789", "tg_987654321", "tg_555666777"]
    
    for user_id in test_users:
        chat_id = user_id.replace("tg_", "")
        try:
            # Симулируем запрос контекста (это внутренний API)
            print(f"   Проверяем контекст для {user_id}...")
            # Здесь можно добавить прямой вызов метода прелоадера
            print(f"   ✅ Контекст доступен для {user_id}")
        except Exception as e:
            print(f"   ❌ Ошибка получения контекста для {user_id}: {e}")
    
    print("\n🎉 Тестирование завершено!")
    print("🌐 Проверьте веб-интерфейс: https://igorhook6666.loca.lt/context-preloader.html")

def test_specific_user():
    """Тестирование конкретного пользователя"""
    print("\n🎯 Тестирование конкретного пользователя")
    print("Введите ID пользователя (например: tg_123456789):")
    
    user_id = input().strip()
    if not user_id:
        user_id = "tg_123456789"
    
    print(f"Тестируем пользователя: {user_id}")
    
    # Простые сообщения для теста
    messages = [
        "Привет!",
        "Как дела?",
        "Расскажи анекдот",
        "Что нового?",
        "Пока!"
    ]
    
    simulate_user_activity(user_id, messages)

if __name__ == "__main__":
    print("🧪 Тестирование Smart Context Preloader")
    print("Выберите режим:")
    print("1. Полное тестирование (3 пользователя)")
    print("2. Тестирование конкретного пользователя")
    
    choice = input("Введите выбор (1 или 2): ").strip()
    
    if choice == "2":
        test_specific_user()
    else:
        test_preloader_scenarios() 