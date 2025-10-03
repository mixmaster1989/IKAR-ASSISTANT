#!/usr/bin/env python3
"""
Тест улучшенного поиска погоды
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_weather_search():
    """Тестируем улучшенный поиск погоды"""
    print("🌤️ ТЕСТ УЛУЧШЕННОГО ПОИСКА ПОГОДЫ")
    print("=" * 50)
    
    try:
        # Импортируем систему интернет-интеллекта
        from internet_intelligence_system import InternetIntelligenceSystem
        
        # Создаем экземпляр системы
        system = InternetIntelligenceSystem()
        
        # Тестовые запросы
        test_queries = [
            "какая погода сегодня в шахтах?",
            "температура в москве",
            "погода завтра в спб",
            "какая погода в ростове на дону"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Тестируем запрос: '{query}'")
            print("-" * 40)
            
            try:
                # Выполняем поиск
                results = await system.search_internet(query, max_total_results=10)
                
                if results:
                    print(f"✅ Найдено {len(results)} результатов:")
                    
                    for i, result in enumerate(results[:5], 1):
                        print(f"\n{i}. {result.title}")
                        print(f"   URL: {result.url}")
                        print(f"   Источник: {result.source}")
                        print(f"   Релевантность: {result.relevance_score:.2f}")
                        print(f"   Сниппет: {result.snippet[:100]}...")
                        
                        # Проверяем релевантность
                        if result.relevance_score < 0.3:
                            print(f"   ⚠️  Низкая релевантность!")
                        elif result.relevance_score > 0.7:
                            print(f"   ✅ Высокая релевантность!")
                else:
                    print("❌ Результаты не найдены")
                    
            except Exception as e:
                print(f"❌ Ошибка при поиске: {e}")
        
        # Тестируем извлечение города
        print(f"\n🏙️ ТЕСТ ИЗВЛЕЧЕНИЯ ГОРОДА")
        print("-" * 40)
        
        test_city_queries = [
            "погода в шахтах",
            "температура москва",
            "какая погода в санкт-петербурге",
            "погода ростов на дону"
        ]
        
        for query in test_city_queries:
            city = system._extract_city_from_query(query)
            print(f"Запрос: '{query}' -> Город: '{city}'")
        
        # Тестируем проверку релевантности
        print(f"\n🎯 ТЕСТ ПРОВЕРКИ РЕЛЕВАНТНОСТИ")
        print("-" * 40)
        
        test_relevance_cases = [
            ("Погода в Шахтах сегодня", "какая погода в шахтах", True),
            ("Breakdown of Code analysis", "какая погода в шахтах", False),
            ("Температура в Москве +15 градусов", "температура москва", True),
            ("GitHub API documentation", "температура москва", False),
        ]
        
        for title, query, expected in test_relevance_cases:
            is_relevant = system._is_result_relevant(title, "", query)
            relevance_score = system._calculate_relevance(title, "", query)
            status = "✅" if is_relevant == expected else "❌"
            print(f"{status} '{title}' для '{query}': релевантность={is_relevant} (ожидалось {expected}), скор={relevance_score:.2f}")
        
        await system.close()
        print(f"\n✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_weather_search()) 