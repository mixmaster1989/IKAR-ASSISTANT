#!/usr/bin/env python3
"""
Быстрый тест инжекции памяти - моментальная проверка
"""

import asyncio
import sys
import os

# Добавляем путь к backend для импортов  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory_injector import get_memory_injector
from core.collective_mind import CollectiveMind
from config import Config


async def quick_test(query: str, show_full_prompt: bool = False, user_id: str = None):
    """Быстрый тест инжекции памяти"""
    
    print(f"🧪 БЫСТРЫЙ ТЕСТ ПАМЯТИ")
    print(f"🔍 Запрос: '{query}'")
    print(f"👤 User ID: {user_id or 'None'}")
    print("-" * 50)
    
    try:
        # Инициализация
        memory_injector = get_memory_injector()
        
        # Анализ потенциала памяти
        print(f"1️⃣ Анализируем потенциал памяти...")
        analysis = await memory_injector.analyze_memory_usage(query, user_id)
        
        # 🔒 ИСПРАВЛЕНИЕ: Передаем user_id в анализ
        if user_id:
            print(f"   👤 Ищем персональную память для user_id: {user_id}")
        
        total_available = analysis.get('total_available', 0)
        top_relevance = analysis.get('top_relevance', 0)
        efficiency = analysis.get('memory_efficiency', 0)
        
        print(f"   📊 Доступно чанков: {total_available}")
        print(f"   📈 Топ релевантность: {top_relevance:.3f}")
        print(f"   ⚡ Эффективность: {efficiency:.1%}")
        
        if total_available == 0:
            print(f"❌ Релевантная память не найдена!")
            # 🔒 ИСПРАВЛЕНИЕ: Попробуем с user_id если не указан
            if not user_id:
                print(f"💡 Попробуйте указать user_id для поиска персональной памяти")
            return
        
        # Инжекция
        print(f"\n2️⃣ Инжектируем память...")
        enhanced_prompt = await memory_injector.inject_memory_into_prompt(
            query, "", user_id, memory_budget_ratio=0.3
        )
        
        original_tokens = len(query.split())
        enhanced_tokens = len(enhanced_prompt.split())
        memory_tokens = enhanced_tokens - original_tokens
        
        print(f"   📝 Оригинал: {original_tokens} токенов")
        print(f"   🚀 Улучшенный: {enhanced_tokens} токенов")
        print(f"   💭 Добавлено памяти: {memory_tokens} токенов ({memory_tokens/enhanced_tokens*100:.1f}%)")
        
        # Показываем добавленную память
        print(f"\n3️⃣ Добавленная память:")
        memory_part = enhanced_prompt[len(query):].strip()
        
        if len(memory_part) > 500:
            print(f"   {memory_part[:500]}...")
            print(f"   [...обрезано, всего {len(memory_part)} символов]")
        else:
            print(f"   {memory_part}")
        
        # Полный промпт (опционально)
        if show_full_prompt:
            print(f"\n4️⃣ ПОЛНЫЙ УЛУЧШЕННЫЙ ПРОМПТ:")
            print(f"{enhanced_prompt}")
        
        print(f"\n✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()


async def interactive_test():
    """Интерактивный режим тестирования"""
    
    print(f"🔧 ИНТЕРАКТИВНЫЙ ТЕСТ ПАМЯТИ")
    print(f"Введите 'exit' для выхода")
    print("=" * 50)
    
    while True:
        try:
            query = input(f"\n🔍 Введите запрос для теста: ").strip()
            
            if query.lower() in ['exit', 'quit', 'выход']:
                print(f"👋 До свидания!")
                break
            
            if not query:
                print(f"❌ Запрос не может быть пустым!")
                continue
            
            # Дополнительные опции
            user_id = input(f"👤 User ID (Enter для пропуска): ").strip()
            user_id = user_id if user_id else None
            
            show_full = input(f"📄 Показать полный промпт? (y/N): ").strip().lower()
            show_full = show_full in ['y', 'yes', 'да']
            
            print()  # Пустая строка для красоты
            
            await quick_test(query, show_full, user_id)
            
        except KeyboardInterrupt:
            print(f"\n👋 Прерывание пользователем. До свидания!")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")


async def batch_test():
    """Пакетный тест для нескольких запросов"""
    
    test_queries = [
        "бот, привет",
        "что ты помнишь о нашей группе",
        "бот, как дела с торговлей", 
        "расскажи про крипту",
        "бот, что нового",
        "помнишь про сервер"
    ]
    
    print(f"🧪 ПАКЕТНЫЙ ТЕСТ ({len(test_queries)} запросов)")
    print("=" * 50)
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Тест {i}/{len(test_queries)}: '{query}'")
        print("-" * 30)
        
        try:
            memory_injector = get_memory_injector()
            analysis = await memory_injector.analyze_memory_usage(query)
            
            total_available = analysis.get('total_available', 0)
            top_relevance = analysis.get('top_relevance', 0)
            
            if total_available > 0:
                enhanced_prompt = await memory_injector.inject_memory_into_prompt(query, "", user_id, memory_budget_ratio=0.3)
                memory_tokens = len(enhanced_prompt.split()) - len(query.split())
                status = "✅ ПАМЯТЬ ДОБАВЛЕНА"
            else:
                memory_tokens = 0
                status = "❌ ПАМЯТЬ НЕ НАЙДЕНА"
            
            print(f"   {status}")
            print(f"   📊 Чанков: {total_available} | Релевантность: {top_relevance:.3f} | Токенов: {memory_tokens}")
            
            results.append({
                'query': query,
                'chunks': total_available,
                'relevance': top_relevance,
                'memory_tokens': memory_tokens,
                'success': total_available > 0
            })
            
        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
            results.append({
                'query': query,
                'chunks': 0,
                'relevance': 0,
                'memory_tokens': 0,
                'success': False,
                'error': str(e)
            })
    
    # Общая статистика
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    successful = [r for r in results if r['success']]
    total_tests = len(results)
    success_rate = len(successful) / total_tests * 100
    
    print(f"   🎯 Успешных тестов: {len(successful)}/{total_tests} ({success_rate:.1f}%)")
    
    if successful:
        avg_chunks = sum(r['chunks'] for r in successful) / len(successful)
        avg_relevance = sum(r['relevance'] for r in successful) / len(successful)
        avg_tokens = sum(r['memory_tokens'] for r in successful) / len(successful)
        
        print(f"   📈 Среднее чанков: {avg_chunks:.1f}")
        print(f"   📈 Средняя релевантность: {avg_relevance:.3f}")
        print(f"   📈 Среднее токенов памяти: {avg_tokens:.0f}")
    
    print(f"\n🏆 ТОП-3 ПО РЕЛЕВАНТНОСТИ:")
    top_results = sorted(successful, key=lambda x: x['relevance'], reverse=True)[:3]
    for i, result in enumerate(top_results, 1):
        print(f"   {i}. '{result['query']}' | Рел: {result['relevance']:.3f} | Чанков: {result['chunks']}")


async def main():
    """Главная функция"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'batch':
            await batch_test()
        elif command == 'interactive':
            await interactive_test()
        else:
            # Прямой тест запроса
            query = ' '.join(sys.argv[1:])
            user_id = None
            # Если последний аргумент похож на user_id (только цифры), используем его
            if len(sys.argv) > 2 and sys.argv[-1].isdigit():
                user_id = sys.argv[-1]
                query = ' '.join(sys.argv[1:-1])  # Убираем user_id из запроса
            await quick_test(query, show_full_prompt=False, user_id=user_id)
    else:
        # Интерактивный режим по умолчанию
        await interactive_test()


if __name__ == "__main__":
    asyncio.run(main())