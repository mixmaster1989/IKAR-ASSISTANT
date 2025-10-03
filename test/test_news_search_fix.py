#!/usr/bin/env python3
"""
🧪 ТЕСТ ИСПРАВЛЕНИЙ ПОИСКА НОВОСТЕЙ
Проверяем, что система правильно обрабатывает запросы о новостях
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

async def test_news_search_fix():
    """Тест исправлений поиска новостей"""
    print("🧪 ТЕСТ ИСПРАВЛЕНИЙ ПОИСКА НОВОСТЕЙ")
    print("=" * 60)
    
    try:
        # Импортируем компоненты
        from ikar_internet_integration import IKARInternetIntegration
        from internet_intelligence_system import InternetIntelligenceSystem
        
        print("✅ Компоненты загружены успешно")
        
        # Тестируем очистку запросов
        print("\n🔧 ТЕСТ 1: Очистка запросов")
        print("-" * 40)
        
        integration = IKARInternetIntegration()
        
        test_queries = [
            "бот, какие новости?",
            "бот, что нового?",
            "бот, что происходит в мире?",
            "бот, расскажи про криптовалюты",
            "бот, погода сегодня"
        ]
        
        for query in test_queries:
            needs_search, search_query, confidence = integration.needs_internet_search(query)
            cleaned_query = integration._clean_search_query(query)
            print(f"   Оригинал: '{query}'")
            print(f"   Очищенный: '{cleaned_query}'")
            print(f"   Нужен поиск: {needs_search} (уверенность: {confidence:.2f})")
            print()
        
        # Тестируем поиск новостей
        print("\n🔍 ТЕСТ 2: Поиск новостей")
        print("-" * 40)
        
        system = InternetIntelligenceSystem()
        
        # Тестируем поиск новостей
        news_query = "последние новости сегодня"
        print(f"Поиск: '{news_query}'")
        
        results = await system.search_internet(news_query, max_total_results=10)
        print(f"✅ Найдено {len(results)} результатов")
        
        # Показываем первые 5 результатов
        for i, result in enumerate(results[:5], 1):
            print(f"   {i}. {result.title}")
            print(f"      URL: {result.url}")
            print(f"      Источник: {result.source}")
            print(f"      Релевантность: {result.relevance_score:.2f}")
            print()
        
        # Тестируем полную обработку
        print("\n🧠 ТЕСТ 3: Полная обработка")
        print("-" * 40)
        
        user_query = "бот, какие новости?"
        print(f"Пользовательский запрос: '{user_query}'")
        
        # Проверяем, нужен ли поиск
        needs_search, search_query, confidence = integration.needs_internet_search(user_query)
        print(f"   Нужен поиск: {needs_search} (уверенность: {confidence:.2f})")
        print(f"   Поисковый запрос: '{search_query}'")
        
        if needs_search:
            # Получаем интернет-информацию
            internet_info = await system.get_internet_intelligence(search_query)
            print(f"   Получена информация (уверенность: {internet_info.confidence_score:.2f})")
            print(f"   Источников: {len(internet_info.sources)}")
            print(f"   AI суммаризация: {internet_info.ai_summary[:200]}...")
            print(f"   Ключевые моменты: {len(internet_info.key_points)}")
        
        print("\n🎯 РЕЗУЛЬТАТ:")
        if needs_search and confidence > 0.7:
            print("✅ СИСТЕМА ПРАВИЛЬНО РАСПОЗНАЕТ ЗАПРОСЫ О НОВОСТЯХ!")
        else:
            print("❌ ПРОБЛЕМА С РАСПОЗНАВАНИЕМ ЗАПРОСОВ О НОВОСТЯХ")
        
        if results and len(results) > 0:
            print("✅ СИСТЕМА НАХОДИТ АКТУАЛЬНЫЕ НОВОСТИ!")
        else:
            print("❌ ПРОБЛЕМА С ПОИСКОМ НОВОСТЕЙ")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_news_search_fix()) 