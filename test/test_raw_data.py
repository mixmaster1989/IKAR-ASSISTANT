#!/usr/bin/env python3
"""
Тест системы с сырыми данными
"""

import json
from simple_internet_system import SimpleInternetSystem

def test_raw_data_system():
    """Тестирование системы с сырыми данными"""
    
    print("🌐 ТЕСТ СИСТЕМЫ С СЫРЫМИ ДАННЫМИ")
    print("=" * 50)
    
    system = SimpleInternetSystem()
    
    # Тест 1: Погода с сырыми данными
    print("\n1️⃣ ТЕСТ ПОГОДЫ (СЫРЫЕ ДАННЫЕ)")
    print("-" * 40)
    
    weather_result = system.search_internet("бот, какая погода в Москве?")
    if weather_result.get('success'):
        data = weather_result['data']
        print(f"Город: {data.get('city')}")
        print(f"Найдено источников: {len(data.get('sources', []))}")
        
        for i, source in enumerate(data.get('sources', [])[:2], 1):
            print(f"\n--- ИСТОЧНИК {i} ---")
            print(f"Заголовок: {source.get('title', 'N/A')}")
            print(f"URL: {source.get('url', 'N/A')}")
            print(f"Контент (первые 200 символов): {source.get('content', 'N/A')[:200]}...")
    else:
        print(f"Ошибка: {weather_result.get('error')}")
    
    # Тест 2: Новости с сырыми данными
    print("\n\n2️⃣ ТЕСТ НОВОСТЕЙ (СЫРЫЕ ДАННЫЕ)")
    print("-" * 40)
    
    news_result = system.search_internet("бот, последние новости России")
    if news_result.get('success'):
        data = news_result['data']
        print(f"Найдено новостей: {len(data)}")
        
        for i, news in enumerate(data[:2], 1):
            print(f"\n--- НОВОСТЬ {i} ---")
            print(f"Заголовок: {news.get('title', 'N/A')}")
            print(f"URL: {news.get('url', 'N/A')}")
            print(f"Контент (первые 200 символов): {news.get('content', 'N/A')[:200]}...")
    else:
        print(f"Ошибка: {news_result.get('error')}")
    
    # Тест 3: Общий поиск с сырыми данными
    print("\n\n3️⃣ ТЕСТ ОБЩЕГО ПОИСКА (СЫРЫЕ ДАННЫЕ)")
    print("-" * 40)
    
    general_result = system.search_internet("бот, что такое блокчейн?")
    if general_result.get('success'):
        data = general_result['data']
        print(f"Найдено результатов: {data.get('results_count', 0)}")
        print(f"Контент (первые 300 символов): {data.get('content', 'N/A')[:300]}...")
        print(f"Источники: {len(data.get('sources', []))}")
    else:
        print(f"Ошибка: {general_result.get('error')}")
    
    print("\n" + "=" * 50)
    print("✅ ТЕСТ ЗАВЕРШЕН")
    print("\n💡 Теперь модель получит сырые данные и сама извлечет нужную информацию!")

if __name__ == "__main__":
    test_raw_data_system() 