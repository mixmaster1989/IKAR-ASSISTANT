#!/usr/bin/env python3
"""
🔍 ТЕСТ ОТЛАДКИ ПОИСКА НОВОСТЕЙ
Проверяем, что именно происходит с поиском новостей и почему возвращается неправильный контент
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

async def test_news_search():
    """Тестируем поиск новостей"""
    print("🔍 ТЕСТ ПОИСКА НОВОСТЕЙ")
    print("=" * 50)
    
    try:
        # Импортируем систему интернет-интеллекта
        from internet_intelligence_system import InternetIntelligenceSystem
        from ikar_internet_integration import IKARInternetIntegration
        
        print("✅ Модули импортированы")
        
        # Инициализируем системы
        internet_system = InternetIntelligenceSystem()
        integration = IKARInternetIntegration()
        
        print("✅ Системы инициализированы")
        
        # Тестируем очистку запроса
        test_query = "бот, какие новости?"
        print(f"\n📝 Тестовый запрос: '{test_query}'")
        
        # Проверяем интеграцию
        needs_search, search_query, confidence = integration.needs_internet_search(test_query)
        print(f"🔍 Нужен поиск: {needs_search}")
        print(f"🔍 Очищенный запрос: '{search_query}'")
        print(f"🔍 Уверенность: {confidence:.2f}")
        
        if needs_search:
            print(f"\n🌐 Выполняем поиск: '{search_query}'")
            
            # Выполняем поиск
            search_results = await internet_system.search_internet(search_query, max_total_results=10)
            print(f"📊 Найдено результатов: {len(search_results)}")
            
            # Показываем первые результаты
            for i, result in enumerate(search_results[:5], 1):
                print(f"\n📄 Результат {i}:")
                print(f"   Заголовок: {result.title}")
                print(f"   URL: {result.url}")
                print(f"   Источник: {result.source}")
                print(f"   Релевантность: {result.relevance_score:.2f}")
                print(f"   Сниппет: {result.snippet[:100]}...")
            
            # Извлекаем контент
            print(f"\n📄 Извлекаем контент...")
            results_with_content = await internet_system.extract_content(search_results)
            
            # Показываем извлеченный контент
            for i, result in enumerate(results_with_content[:3], 1):
                print(f"\n📄 Контент {i}:")
                print(f"   URL: {result.url}")
                if result.content:
                    print(f"   Контент (первые 200 симв.): {result.content[:200]}...")
                else:
                    print(f"   ❌ Контент не извлечен")
            
            # Обрабатываем через AI
            print(f"\n🧠 Обрабатываем через AI...")
            processed_info = await internet_system.process_with_ai(search_query, results_with_content)
            
            print(f"\n📊 Результат обработки:")
            print(f"   Уверенность: {processed_info.confidence_score:.2f}")
            print(f"   Источников: {len(processed_info.sources)}")
            print(f"   Время обработки: {processed_info.processing_time:.2f}с")
            
            print(f"\n📝 AI-выжимка:")
            print(f"{processed_info.ai_summary}")
            
            print(f"\n🔑 Ключевые моменты:")
            for i, point in enumerate(processed_info.key_points[:3], 1):
                print(f"   {i}. {point}")
            
            print(f"\n📚 Источники:")
            for i, source in enumerate(processed_info.sources[:3], 1):
                print(f"   {i}. {source}")
        
        else:
            print("❌ Поиск не требуется")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

async def test_news_sources():
    """Тестируем источники новостей отдельно"""
    print("\n\n🔍 ТЕСТ ИСТОЧНИКОВ НОВОСТЕЙ")
    print("=" * 50)
    
    try:
        from internet_intelligence_system import InternetIntelligenceSystem
        
        internet_system = InternetIntelligenceSystem()
        
        # Тестируем поиск новостей напрямую
        print("🌐 Тестируем поиск новостей...")
        news_results = await internet_system._search_news("новости сегодня", max_results=5)
        
        print(f"📊 Найдено новостей: {len(news_results)}")
        
        for i, result in enumerate(news_results, 1):
            print(f"\n📰 Новость {i}:")
            print(f"   Заголовок: {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Источник: {result.source}")
            print(f"   Релевантность: {result.relevance_score:.2f}")
            print(f"   Дата: {result.timestamp}")
            print(f"   Сниппет: {result.snippet[:100]}...")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТА ОТЛАДКИ ПОИСКА НОВОСТЕЙ")
    print("=" * 60)
    
    await test_news_search()
    await test_news_sources()
    
    print("\n✅ ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    asyncio.run(main()) 