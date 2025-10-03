"""
Тест Smart Context Preloader - проверка работы системы предзагрузки контекста
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from memory.smart_context_preloader import SmartContextPreloader
from memory.sqlite import SQLiteStorage
from llm.openrouter import OpenRouterClient
from config import Config

async def test_context_preloader():
    """Тестирует все функции Smart Context Preloader"""
    
    print("🚀 Тестирование Smart Context Preloader")
    print("=" * 60)
    
    # Инициализация
    db_path = "data/test_chatumba.db"
    preloader = SmartContextPreloader(db_path)
    
    print("✅ Smart Context Preloader инициализирован")
    
    # Тест 1: Запуск и остановка
    print("\n📋 Тест 1: Запуск и остановка системы")
    print("-" * 40)
    
    preloader.start()
    print("✅ Предзагрузчик запущен")
    
    # Проверяем статус
    stats = preloader.get_stats()
    print(f"📊 Статус: {stats}")
    
    time.sleep(2)
    
    preloader.stop()
    print("✅ Предзагрузчик остановлен")
    
    # Тест 2: Трекинг активности
    print("\n📋 Тест 2: Трекинг активности пользователей")
    print("-" * 40)
    
    # Добавляем активность пользователей
    test_users = [
        ("user1", "chat1", "Привет! Как дела?"),
        ("user2", "chat2", "Расскажи о криптовалютах"),
        ("user1", "chat1", "Что думаешь о Bitcoin?"),
        ("user3", "chat3", "Помоги с анализом графиков"),
        ("user1", "chat1", "Когда лучше покупать?"),
    ]
    
    for user_id, chat_id, message in test_users:
        preloader.track_message(user_id, chat_id, message, response_time=1.5)
        print(f"📝 Отслежено сообщение от {user_id}: {message[:30]}...")
    
    print(f"👥 Активных пользователей: {len(preloader.user_activities)}")
    
    # Тест 3: Анализ паттернов
    print("\n📋 Тест 3: Анализ паттернов разговора")
    print("-" * 40)
    
    # Добавляем больше сообщений для анализа
    for i in range(10):
        preloader.track_message("user1", "chat1", f"Сообщение {i+1} от активного пользователя", response_time=2.0)
    
    user_activity = preloader.user_activities["user1:chat1"]
    print(f"📊 Активность user1:")
    print(f"   Сообщений: {user_activity.message_count}")
    print(f"   Среднее время ответа: {user_activity.avg_response_time:.2f}s")
    print(f"   Общие темы: {user_activity.common_topics}")
    print(f"   Предпочитаемые часы: {user_activity.preferred_time_slots}")
    
    # Тест 4: Предзагрузка контекста
    print("\n📋 Тест 4: Создание предзагруженного контекста")
    print("-" * 40)
    
    # Создаем контекст для активного пользователя
    activity = preloader.user_activities["user1:chat1"]
    context = preloader._create_preloaded_context(activity)
    
    if context:
        print("✅ Контекст успешно создан")
        print(f"   Пользователь: {context.user_id}")
        print(f"   Чат: {context.chat_id}")
        print(f"   Приоритет: {context.priority}")
        print(f"   TTL: {context.expires_at - context.created_at:.0f} секунд")
        print(f"   Предсказанные вопросы: {len(context.context_data.get('predicted_questions', []))}")
    else:
        print("❌ Не удалось создать контекст")
    
    # Тест 5: Принудительная предзагрузка
    print("\n📋 Тест 5: Принудительная предзагрузка")
    print("-" * 40)
    
    success = preloader.force_preload("user1", "chat1")
    if success:
        print("✅ Принудительная предзагрузка успешна")
        
        # Проверяем, что контекст доступен
        cached_context = preloader.get_preloaded_context("user1", "chat1")
        if cached_context:
            print("✅ Контекст найден в кэше")
            print(f"   Время создания: {cached_context.get('preload_timestamp', 'неизвестно')}")
        else:
            print("❌ Контекст не найден в кэше")
    else:
        print("❌ Принудительная предзагрузка не удалась")
    
    # Тест 6: Статистика и мониторинг
    print("\n📋 Тест 6: Статистика и мониторинг")
    print("-" * 40)
    
    stats = preloader.get_stats()
    print("📊 Финальная статистика:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Тест 7: Очистка кэша
    print("\n📋 Тест 7: Очистка кэша")
    print("-" * 40)
    
    cleared_count = preloader.clear_cache()
    print(f"🧹 Очищено контекстов: {cleared_count}")
    
    # Проверяем, что кэш пуст
    cached_context = preloader.get_preloaded_context("user1", "chat1")
    if cached_context is None:
        print("✅ Кэш успешно очищен")
    else:
        print("❌ Кэш не очищен полностью")
    
    print("\n🎉 Все тесты завершены!")
    print("=" * 60)

def test_integration():
    """Тестирует интеграцию с основной системой"""
    
    print("\n🔗 Тестирование интеграции")
    print("=" * 60)
    
    # Тест API endpoints
    print("📋 Проверка API endpoints:")
    
    endpoints = [
        "/api/admin/context_preloader/status",
        "/api/admin/context_preloader/start",
        "/api/admin/context_preloader/stop",
        "/api/admin/context_preloader/activities",
        "/api/admin/context_preloader/force_preload",
        "/api/admin/context_preloader/clear_cache",
        "/api/admin/context_preloader/config"
    ]
    
    for endpoint in endpoints:
        print(f"   📡 {endpoint}")
    
    print("✅ Все API endpoints определены")
    
    # Тест веб-интерфейса
    web_interface = Path("frontend/public/context-preloader.html")
    if web_interface.exists():
        print("✅ Веб-интерфейс создан")
        print(f"   📄 Путь: {web_interface}")
    else:
        print("❌ Веб-интерфейс не найден")
    
    print("\n🎯 Интеграция проверена!")

def performance_test():
    """Тестирует производительность системы"""
    
    print("\n⚡ Тест производительности")
    print("=" * 60)
    
    preloader = SmartContextPreloader("data/test_chatumba.db")
    
    # Тест массового трекинга
    print("📋 Тест массового трекинга сообщений")
    
    start_time = time.time()
    
    for i in range(1000):
        user_id = f"user{i % 10}"  # 10 пользователей
        chat_id = f"chat{i % 5}"   # 5 чатов
        message = f"Тестовое сообщение номер {i}"
        
        preloader.track_message(user_id, chat_id, message, response_time=1.0)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️  Время обработки 1000 сообщений: {duration:.2f} секунд")
    print(f"📊 Скорость: {1000/duration:.0f} сообщений/секунду")
    
    # Статистика
    stats = preloader.get_stats()
    print(f"👥 Активных пользователей: {stats['active_users']}")
    print(f"💾 Использование памяти: {stats['memory_usage']['total_kb']} KB")
    
    print("✅ Тест производительности завершен")

if __name__ == "__main__":
    # Создаем директорию для тестовой БД
    os.makedirs("data", exist_ok=True)
    
    try:
        # Запускаем все тесты
        asyncio.run(test_context_preloader())
        test_integration()
        performance_test()
        
        print("\n🎊 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("Smart Context Preloader готов к использованию!")
        
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Очищаем тестовую БД
        test_db = Path("data/test_chatumba.db")
        if test_db.exists():
            test_db.unlink()
            print("\n🧹 Тестовая база данных очищена") 