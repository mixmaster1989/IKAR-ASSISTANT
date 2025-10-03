#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы оптимизатора памяти.
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем backend в путь
sys.path.append(str(Path(__file__).parent / "backend"))

from memory.memory_optimizer import MemoryOptimizer, test_optimization
from memory.sqlite import SQLiteStorage
from llm.openrouter import OpenRouterClient
from config import Config
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_memory_optimizer():
    """Тестирует работу оптимизатора памяти."""
    print("🧪 Тестирование оптимизатора памяти...")
    
    try:
        # Инициализация компонентов через менеджер
        from backend.utils.component_manager import get_component_manager
        component_manager = get_component_manager()
        
        config = component_manager.get_config()
        sqlite_storage = component_manager.get_sqlite_storage()
        llm_client = component_manager.get_llm_client()
        
        print(f"📁 База данных: {sqlite_storage.db_path}")
        
        # Создаем оптимизатор
        optimizer = MemoryOptimizer(sqlite_storage.db_path, llm_client, max_chunk_tokens=30000)
        
        # Тестируем определение ночного времени
        print(f"🌙 Ночное время: {optimizer.is_night_time()}")
        print(f"⏰ Ночные часы: {optimizer.night_start} - {optimizer.night_end}")
        
        # Получаем статистику
        stats = await optimizer.get_optimization_stats()
        print(f"📊 Статистика:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Получаем чанки для оптимизации
        chunks = await optimizer.get_memory_chunks(limit=3)
        print(f"📦 Найдено чанков для оптимизации: {len(chunks)}")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"   Чанк {i}: {chunk['source']}, токенов: {chunk['tokens']}")
        
        if chunks:
            print("\n🔄 Тестируем оптимизацию первого чанка...")
            
            # Принудительно включаем ночное время для теста
            original_is_night_time = optimizer.is_night_time
            optimizer.is_night_time = lambda: True
            
            try:
                # Тестируем оптимизацию одного чанка
                first_chunk = chunks[0]
                print(f"📝 Оптимизируем: {first_chunk['source']}")
                
                optimized_content = await optimizer.optimize_chunk(first_chunk)
                
                if optimized_content:
                    original_tokens = optimizer.count_tokens(first_chunk['content'])
                    optimized_tokens = optimizer.count_tokens(optimized_content)
                    compression_ratio = original_tokens / optimized_tokens if optimized_tokens > 0 else 1
                    
                    print(f"✅ Оптимизация успешна!")
                    print(f"   Исходный размер: {original_tokens} токенов")
                    print(f"   Оптимизированный размер: {optimized_tokens} токенов")
                    print(f"   Коэффициент сжатия: {compression_ratio:.2f}x")
                    
                    # Показываем начало оптимизированного текста
                    preview = optimized_content[:200] + "..." if len(optimized_content) > 200 else optimized_content
                    print(f"   Превью: {preview}")
                    
                    # Предлагаем сохранить (для демонстрации)
                    save_choice = input("\n💾 Сохранить оптимизированный чанк? (y/N): ").lower()
                    if save_choice == 'y':
                        success = await optimizer.save_optimized_chunk(first_chunk, optimized_content)
                        if success:
                            print("✅ Чанк сохранен!")
                        else:
                            print("❌ Ошибка сохранения")
                    else:
                        print("🚫 Сохранение отменено")
                else:
                    print("❌ Ошибка оптимизации")
                    
            finally:
                # Восстанавливаем оригинальную функцию
                optimizer.is_night_time = original_is_night_time
        else:
            print("ℹ️  Нет чанков для оптимизации")
            print("   Возможно, база данных пуста или все данные уже оптимизированы")
        
        print("\n🎯 Тест завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

async def test_full_cycle():
    """Тестирует полный цикл оптимизации."""
    print("\n🔄 Тестирование полного цикла оптимизации...")
    
    try:
        # Используем компоненты из менеджера
        from backend.utils.component_manager import get_component_manager
        component_manager = get_component_manager()
        
        config = component_manager.get_config()
        sqlite_storage = component_manager.get_sqlite_storage()
        llm_client = component_manager.get_llm_client()
        
        # Запускаем тестовую оптимизацию
        await test_optimization(sqlite_storage.db_path, llm_client)
        print("✅ Полный цикл оптимизации выполнен!")
        
    except Exception as e:
        print(f"❌ Ошибка полного цикла: {e}")

def print_usage():
    """Выводит справку по использованию."""
    print("""
🧠 Тестовый скрипт оптимизатора памяти

Использование:
    python test_memory_optimizer.py [команда]

Команды:
    test        - Полный тест оптимизатора (по умолчанию)
    cycle       - Тест одного цикла оптимизации
    help        - Показать эту справку

Примеры:
    python test_memory_optimizer.py
    python test_memory_optimizer.py test
    python test_memory_optimizer.py cycle
    """)

async def main():
    """Главная функция."""
    command = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    if command == "help":
        print_usage()
        return
    elif command == "test":
        await test_memory_optimizer()
    elif command == "cycle":
        await test_full_cycle()
    else:
        print(f"❌ Неизвестная команда: {command}")
        print_usage()
        return

if __name__ == "__main__":
    asyncio.run(main()) 