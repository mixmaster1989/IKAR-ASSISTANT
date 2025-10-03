#!/usr/bin/env python3
"""
Тест новой простой системы интернет-интеллекта
"""

import asyncio
import json
from simple_internet_system import SimpleInternetSystem

async def test_simple_internet():
    """Тестирование новой системы интернет-интеллекта"""
    
    print("🌐 ТЕСТИРОВАНИЕ НОВОЙ ПРОСТОЙ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА")
    print("=" * 60)
    
    system = SimpleInternetSystem()
    
    # Тест 1: Поиск погоды
    print("\n1️⃣ ТЕСТ ПОИСКА ПОГОДЫ")
    print("-" * 30)
    
    weather_queries = [
        "бот, какая погода в Москве?",
        "бот, погода в Санкт-Петербурге",
        "бот, температура в Ростове-на-Дону"
    ]
    
    for query in weather_queries:
        print(f"\nЗапрос: {query}")
        result = system.search_internet(query)
        print(f"Тип: {result.get('type')}")
        print(f"Успех: {result.get('success')}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            print(f"Город: {data.get('city')}")
            print(f"Температура: {data.get('temperature')}")
            print(f"Описание: {data.get('description')}")
            print(f"Источник: {data.get('source')}")
        else:
            print(f"Ошибка: {result.get('error')}")
    
    # Тест 2: Поиск новостей
    print("\n\n2️⃣ ТЕСТ ПОИСКА НОВОСТЕЙ")
    print("-" * 30)
    
    news_queries = [
        "бот, какие новости?",
        "бот, последние новости о технологиях",
        "бот, что происходит в мире?"
    ]
    
    for query in news_queries:
        print(f"\nЗапрос: {query}")
        result = system.search_internet(query)
        print(f"Тип: {result.get('type')}")
        print(f"Успех: {result.get('success')}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            print(f"Найдено новостей: {len(data)}")
            for i, news in enumerate(data[:2], 1):
                print(f"  {i}. {news.get('title', 'Без заголовка')}")
                print(f"     URL: {news.get('url', 'N/A')}")
        else:
            print(f"Ошибка: {result.get('error')}")
    
    # Тест 3: Общий поиск
    print("\n\n3️⃣ ТЕСТ ОБЩЕГО ПОИСКА")
    print("-" * 30)
    
    general_queries = [
        "бот, что такое искусственный интеллект?",
        "бот, кто такой Илон Маск?",
        "бот, как работает блокчейн?"
    ]
    
    for query in general_queries:
        print(f"\nЗапрос: {query}")
        result = system.search_internet(query)
        print(f"Тип: {result.get('type')}")
        print(f"Успех: {result.get('success')}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            print(f"Найдено результатов: {data.get('results_count', 0)}")
            print(f"Сводка: {data.get('summary', 'N/A')[:200]}...")
            print(f"Источники: {len(data.get('sources', []))}")
        else:
            print(f"Ошибка: {result.get('error')}")
    
    # Тест 4: Очистка запросов
    print("\n\n4️⃣ ТЕСТ ОЧИСТКИ ЗАПРОСОВ")
    print("-" * 30)
    
    test_queries = [
        "бот, какая погода?",
        "БОТ, НОВОСТИ!",
        "боту, что нового?",
        "ботом, расскажи о технологиях"
    ]
    
    for query in test_queries:
        cleaned = system.clean_query(query)
        print(f"Оригинал: '{query}'")
        print(f"Очищенный: '{cleaned}'")
        print()
    
    # Тест 5: Определение типа запроса
    print("\n\n5️⃣ ТЕСТ ОПРЕДЕЛЕНИЯ ТИПА ЗАПРОСА")
    print("-" * 30)
    
    type_test_queries = [
        "погода в Москве",
        "последние новости",
        "что такое ИИ",
        "температура воздуха",
        "что происходит в мире"
    ]
    
    for query in type_test_queries:
        query_type = system.detect_query_type(query)
        print(f"Запрос: '{query}' -> Тип: {query_type}")
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    asyncio.run(test_simple_internet()) 