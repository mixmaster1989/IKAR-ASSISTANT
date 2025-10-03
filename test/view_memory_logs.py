#!/usr/bin/env python3
"""
Скрипт для просмотра детальных логов инъекции памяти
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к backend
sys.path.append('backend')

async def view_memory_injection_details():
    """Показывает детали инъекции памяти"""
    
    print("🔍 Детальный анализ инъекции памяти\n")
    
    try:
        from backend.core.memory_injector import get_memory_injector
        from backend.core.collective_mind import get_collective_mind
        
        injector = get_memory_injector()
        collective_mind = get_collective_mind()
        
        # Тестовые промпты для анализа
        test_prompts = [
            "Как работает криптовалюта?",
            "Объясни технический анализ",
            "Что такое блокчейн?",
            "Как торговать на бирже?"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"📝 Анализ промпта {i}: {prompt}")
            print("-" * 60)
            
            # Анализ потенциала памяти
            memory_analysis = await injector.analyze_memory_usage(prompt)
            
            print(f"🔍 Найдено чанков: {memory_analysis.get('total_available', 0)}")
            print(f"📊 Токенов: {memory_analysis.get('token_usage', 0):,}")
            print(f"⭐ Топ релевантность: {memory_analysis.get('top_relevance', 0):.2f}")
            print(f"⚡ Эффективность: {memory_analysis.get('memory_efficiency', 0):.1f}")
            
            # Распределение по релевантности
            relevance_dist = memory_analysis.get('relevance_distribution', {})
            if relevance_dist:
                print(f"📈 Релевантность:")
                print(f"   🔴 Высокая (>0.7): {relevance_dist.get('high', 0)}")
                print(f"   🟡 Средняя (0.3-0.7): {relevance_dist.get('medium', 0)}")
                print(f"   🟢 Низкая (<0.3): {relevance_dist.get('low', 0)}")
            
            # Распределение по типам
            type_dist = memory_analysis.get('type_distribution', {})
            if type_dist:
                print(f"🏷️ Типы памяти:")
                for memory_type, count in type_dist.items():
                    type_names = {
                        'insight': 'Инсайты',
                        'wisdom': 'Мудрость',
                        'experience': 'Опыт',
                        'observation': 'Наблюдения',
                        'reflection': 'Размышления'
                    }
                    name = type_names.get(memory_type, memory_type)
                    print(f"   📚 {name}: {count}")
            
            print()
            
            # Показываем пример инъекции (без реальной генерации)
            if memory_analysis.get('total_available', 0) > 0:
                print("💉 Пример инъекции памяти:")
                memory_chunks = await injector.select_relevant_memories(prompt, "")
                
                for j, chunk in enumerate(memory_chunks[:3], 1):  # Показываем топ-3
                    stars = "⭐" * min(int(chunk.relevance_score * 5), 5)
                    print(f"   {j}. {stars} (Релевантность: {chunk.relevance_score:.2f})")
                    print(f"      Тип: {chunk.memory_type}")
                    print(f"      Токены: {chunk.tokens_count}")
                    print(f"      Содержимое: {chunk.content[:100]}...")
                    print()
            
            print("=" * 60)
            print()
        
        # Статистика коллективной памяти
        print("📊 Статистика коллективной памяти:")
        try:
            # Получаем общую статистику
            total_memories = 0
            memory_types = {}
            
            # Здесь можно добавить запрос к БД для получения статистики
            print("   📈 Общая статистика:")
            print("      (Для получения точной статистики нужен доступ к БД)")
            
        except Exception as e:
            print(f"   ❌ Ошибка получения статистики: {e}")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def view_log_files():
    """Показывает логи системы"""
    print("📋 Логи системы:")
    
    log_files = [
        "logs/chatumba.log",
        "logs/memory.log", 
        "logs/error.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📄 {log_file}:")
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Показываем последние 10 строк с упоминанием памяти
                    memory_lines = [line for line in lines if 'память' in line.lower() or 'memory' in line.lower() or 'инъекция' in line.lower()]
                    
                    if memory_lines:
                        print("   Последние записи о памяти:")
                        for line in memory_lines[-5:]:  # Последние 5
                            print(f"   {line.strip()}")
                    else:
                        print("   Записей о памяти не найдено")
                        
            except Exception as e:
                print(f"   ❌ Ошибка чтения: {e}")
        else:
            print(f"\n❌ Файл не найден: {log_file}")

if __name__ == "__main__":
    print("🧠 Анализ системы инъекции памяти\n")
    
    # Анализ деталей
    asyncio.run(view_memory_injection_details())
    
    # Просмотр логов
    view_log_files()
    
    print("\n💡 Для просмотра логов в реальном времени:")
    print("   tail -f logs/chatumba.log | grep -i память")
    print("   tail -f logs/memory.log") 