"""
Тест для LazyMemory - проверка замены vector_store
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from memory.lazy_memory import LazyMemory, get_lazy_memory
from utils.component_manager import get_component_manager


def test_lazy_memory_basic():
    """Базовый тест LazyMemory"""
    print("🧪 Тест 1: Базовый функционал LazyMemory")
    
    try:
        # Создаем экземпляр
        lazy_memory = LazyMemory()
        print("✅ LazyMemory создан успешно")
        
        # Тестируем добавление сообщений
        user_id = "test_user_123"
        chat_id = "test_chat_456"
        
        # Добавляем несколько сообщений
        lazy_memory.add_message(user_id, chat_id, "Привет! Как дела?")
        lazy_memory.add_message(user_id, chat_id, "Я изучаю криптовалюты")
        lazy_memory.add_message(user_id, chat_id, "Bitcoin сегодня растет")
        lazy_memory.add_message(user_id, chat_id, "Погода сегодня хорошая")
        
        print("✅ Сообщения добавлены")
        
        # Тестируем поиск
        results = lazy_memory.get_relevant_history(user_id, "криптовалюты", limit=5)
        print(f"✅ Поиск по 'криптовалюты': найдено {len(results)} результатов")
        
        for i, result in enumerate(results):
            print(f"  {i+1}. {result['content'][:50]}...")
        
        # Тестируем поиск по Bitcoin
        results = lazy_memory.get_relevant_history(user_id, "Bitcoin", limit=3)
        print(f"✅ Поиск по 'Bitcoin': найдено {len(results)} результатов")
        
        # Тестируем статистику
        stats = lazy_memory.get_memory_stats(user_id)
        print(f"✅ Статистика: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в базовом тесте: {e}")
        return False


def test_lazy_memory_singleton():
    """Тест синглтона LazyMemory"""
    print("\n🧪 Тест 2: Синглтон LazyMemory")
    
    try:
        # Получаем два экземпляра
        instance1 = get_lazy_memory()
        instance2 = get_lazy_memory()
        
        # Проверяем что это один и тот же объект
        if instance1 is instance2:
            print("✅ Синглтон работает корректно")
            return True
        else:
            print("❌ Синглтон не работает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте синглтона: {e}")
        return False


def test_component_manager_integration():
    """Тест интеграции с ComponentManager"""
    print("\n🧪 Тест 3: Интеграция с ComponentManager")
    
    try:
        # Получаем ComponentManager
        component_manager = get_component_manager()
        
        # Получаем LazyMemory через ComponentManager
        lazy_memory = component_manager.get_lazy_memory()
        print("✅ LazyMemory получен через ComponentManager")
        
        # Проверяем что get_vector_store возвращает LazyMemory
        vector_store = component_manager.get_vector_store()
        if hasattr(vector_store, 'get_relevant_history'):
            print("✅ get_vector_store возвращает LazyMemory (обратная совместимость)")
            return True
        else:
            print("❌ get_vector_store не возвращает LazyMemory")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте интеграции: {e}")
        return False


def test_memory_injector_integration():
    """Тест интеграции с MemoryInjector"""
    print("\n🧪 Тест 4: Интеграция с MemoryInjector")
    
    try:
        from core.memory_injector import get_memory_injector
        
        # Получаем MemoryInjector
        memory_injector = get_memory_injector()
        print("✅ MemoryInjector получен")
        
        # Тестируем инъекцию памяти
        user_id = "test_user_456"
        query = "криптовалюты"
        
        # Добавляем тестовые данные в LazyMemory
        lazy_memory = get_lazy_memory()
        lazy_memory.add_message(user_id, "chat", "Я интересуюсь криптовалютами")
        lazy_memory.add_message(user_id, "chat", "Bitcoin и Ethereum популярны")
        
        # Тестируем выбор релевантной памяти
        memories = asyncio.run(memory_injector.select_relevant_memories(
            query, "", user_id, max_memories=5
        ))
        
        print(f"✅ MemoryInjector нашел {len(memories)} релевантных воспоминаний")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте MemoryInjector: {e}")
        return False


def test_api_routes_integration():
    """Тест интеграции с API routes"""
    print("\n🧪 Тест 5: Интеграция с API routes")
    
    try:
        # Имитируем работу API routes
        from memory.lazy_memory import get_lazy_memory
        
        lazy_memory = get_lazy_memory()
        user_id = "test_user_789"
        
        # Добавляем сообщения
        lazy_memory.add_message(user_id, "chat", "Привет! Как дела?")
        lazy_memory.add_message(user_id, "chat", "Расскажи про криптовалюты")
        
        # Имитируем поиск как в routes.py
        memory_query = "криптовалюты"
        memories = lazy_memory.get_relevant_history(user_id, memory_query, limit=3)
        
        print(f"✅ API routes интеграция: найдено {len(memories)} воспоминаний")
        
        # Проверяем формат данных
        if memories and 'content' in memories[0]:
            print("✅ Формат данных корректный")
            return True
        else:
            print("❌ Неправильный формат данных")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте API routes: {e}")
        return False


def cleanup_test_data():
    """Очистка тестовых данных"""
    print("\n🧹 Очистка тестовых данных")
    
    try:
        # Удаляем тестовую базу данных
        import os
        if os.path.exists("chatumba.db"):
            os.remove("chatumba.db")
            print("✅ Тестовая база данных удалена")
        
        # Очищаем кэш LazyMemory
        lazy_memory = get_lazy_memory()
        lazy_memory.cache.clear()
        print("✅ Кэш LazyMemory очищен")
        
    except Exception as e:
        print(f"⚠️ Ошибка при очистке: {e}")


def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТОВ LazyMemory")
    print("=" * 50)
    
    tests = [
        test_lazy_memory_basic,
        test_lazy_memory_singleton,
        test_component_manager_integration,
        test_memory_injector_integration,
        test_api_routes_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! LazyMemory работает корректно!")
        return True
    else:
        print("⚠️ Некоторые тесты не прошли. Проверьте логи выше.")
        return False


if __name__ == "__main__":
    success = main()
    cleanup_test_data()
    
    if success:
        print("\n✅ LazyMemory готов к использованию!")
        print("🔄 Можно удалять мертвый код vector_store")
    else:
        print("\n❌ Есть проблемы с LazyMemory. Исправьте перед удалением vector_store")
    
    sys.exit(0 if success else 1) 