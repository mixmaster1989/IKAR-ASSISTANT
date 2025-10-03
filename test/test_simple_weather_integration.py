#!/usr/bin/env python3
"""
Простой тест интеграции поиска погоды
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_simple_weather_integration():
    """Тестируем основную функциональность поиска погоды"""
    print("🌤️ ПРОСТОЙ ТЕСТ ИНТЕГРАЦИИ ПОИСКА ПОГОДЫ")
    print("=" * 50)
    
    try:
        # Импортируем необходимые модули
        from ikar_internet_integration import IKARInternetIntegration
        from internet_intelligence_system import InternetIntelligenceSystem
        
        # Тестовые сообщения
        test_messages = [
            "бот, какая погода сегодня в шахтах?",
            "бот, температура в москве",
            "бот, погода завтра в спб",
            "бот, какая погода в ростове на дону"
        ]
        
        # Создаем экземпляры систем
        system = InternetIntelligenceSystem()
        integration = IKARInternetIntegration()
        
        for message in test_messages:
            print(f"\n🔍 Тестируем сообщение: '{message}'")
            print("-" * 40)
            
            try:
                # Очищаем запрос
                cleaned_query = integration._clean_search_query(message)
                print(f"📝 Очищенный запрос: '{cleaned_query}'")
                
                # Проверяем, что "бот" убран из запроса
                if "бот" in cleaned_query.lower():
                    print("❌ ОШИБКА: 'бот' не убран из запроса!")
                else:
                    print("✅ 'бот' успешно убран из запроса")
                
                # Проверяем, что запрос содержит погодные ключевые слова
                weather_keywords = ["погода", "температура", "градус"]
                has_weather_keywords = any(keyword in cleaned_query.lower() for keyword in weather_keywords)
                
                if has_weather_keywords:
                    print("✅ Обнаружены погодные ключевые слова")
                else:
                    print("⚠️  Не обнаружены погодные ключевые слова")
                
                # Проверяем извлечение города
                city = system._extract_city_from_query(cleaned_query)
                
                if city:
                    print(f"🏙️ Извлечен город: '{city}'")
                else:
                    print("⚠️  Город не извлечен")
                
                # Проверяем необходимость интернет-поиска
                weather_keywords = ["погода", "температура", "градус", "холодно", "тепло", "дождь", "снег"]
                needs_internet = any(keyword in cleaned_query.lower() for keyword in weather_keywords)
                
                if needs_internet:
                    print("✅ Интернет-поиск необходим")
                    
                    # Выполняем быстрый поиск (только первые 3 результата)
                    print("🔍 Выполняем быстрый поиск...")
                    results = await system.search_internet(cleaned_query, max_total_results=3)
                    
                    if results:
                        print(f"✅ Найдено {len(results)} результатов:")
                        for i, result in enumerate(results[:2], 1):
                            print(f"   {i}. {result.title}")
                            print(f"      Релевантность: {result.relevance_score:.2f}")
                            if result.relevance_score > 0.7:
                                print(f"      ✅ Высокая релевантность!")
                    else:
                        print("❌ Результаты не найдены")
                else:
                    print("⚠️  Интернет-поиск не требуется")
                
            except Exception as e:
                print(f"❌ Ошибка при обработке: {e}")
        
        await system.close()
        print(f"\n✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_weather_integration()) 