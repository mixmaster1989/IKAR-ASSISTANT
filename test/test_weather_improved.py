#!/usr/bin/env python3
"""
Краткий тест улучшенной системы интернет-интеллекта
"""

import json
from simple_internet_system import SimpleInternetSystem

def test_improvements():
    """Тестирование улучшений"""
    
    print("🌐 ТЕСТ УЛУЧШЕННОЙ СИСТЕМЫ")
    print("=" * 40)
    
    system = SimpleInternetSystem()
    
    # Тест 1: Улучшенное извлечение температуры
    print("\n1️⃣ ТЕСТ ИЗВЛЕЧЕНИЯ ТЕМПЕРАТУРЫ")
    print("-" * 30)
    
    weather_result = system.search_internet("бот, какая погода в Москве?")
    if weather_result.get('success'):
        data = weather_result['data']
        print(f"Город: {data.get('city')}")
        print(f"Температура: {data.get('temperature')}")
        print(f"Описание: {data.get('description')}")
        print(f"Источник: {data.get('source')}")
    else:
        print(f"Ошибка: {weather_result.get('error')}")
    
    # Тест 2: Фильтрация новостей
    print("\n2️⃣ ТЕСТ ФИЛЬТРАЦИИ НОВОСТЕЙ")
    print("-" * 30)
    
    news_result = system.search_internet("бот, последние новости России")
    if news_result.get('success'):
        data = news_result['data']
        print(f"Найдено новостей: {len(data)}")
        for i, news in enumerate(data[:2], 1):
            print(f"  {i}. {news.get('title', 'Без заголовка')}")
            print(f"     URL: {news.get('url', 'N/A')}")
    else:
        print(f"Ошибка: {news_result.get('error')}")
    
    # Тест 3: Общий поиск
    print("\n3️⃣ ТЕСТ ОБЩЕГО ПОИСКА")
    print("-" * 30)
    
    general_result = system.search_internet("бот, что такое блокчейн?")
    if general_result.get('success'):
        data = general_result['data']
        print(f"Найдено результатов: {data.get('results_count', 0)}")
        print(f"Сводка: {data.get('summary', 'N/A')[:200]}...")
        print(f"Источники: {len(data.get('sources', []))}")
    else:
        print(f"Ошибка: {general_result.get('error')}")
    
    print("\n" + "=" * 40)
    print("✅ ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_improvements() 