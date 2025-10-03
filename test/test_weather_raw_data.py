"""
Тест для вывода всех сырых данных погоды
Показывает что именно парсит система для Шахт и Ростова
"""

import sys
import os
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from simple_internet_system import SimpleInternetSystem

def test_weather_raw_data():
    """Тестирует и выводит все сырые данные погоды"""
    
    print("🔥 ТЕСТ СЫРЫХ ДАННЫХ ПОГОДЫ")
    print("=" * 80)
    
    # Инициализируем систему
    internet_system = SimpleInternetSystem()
    
    # Тестируем Шахты
    print("\n📍 ТЕСТ 1: ПОГОДА В ШАХТАХ")
    print("-" * 50)
    
    try:
        result = internet_system.search_internet("погода в шахтах")
        print(f"✅ Результат получен: {result.get('success', False)}")
        print(f"Тип: {result.get('type', 'unknown')}")
        
        if result.get('success') and result.get('data', {}).get('sources'):
            sources = result['data']['sources']
            print(f"Найдено источников: {len(sources)}")
            
            print("\n📊 СЫРЫЕ ДАННЫЕ:")
            for i, source in enumerate(sources, 1):
                print(f"\n--- ИСТОЧНИК {i} ---")
                print(f"Заголовок: {source.get('title', 'НЕТ')}")
                print(f"URL: {source.get('url', 'НЕТ')}")
                print(f"Контент (первые 500 символов):")
                content = source.get('content', 'НЕТ КОНТЕНТА')
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-" * 40)
        else:
            print("❌ Источники не найдены")
            if result.get('error'):
                print(f"Ошибка: {result['error']}")
            if result.get('data'):
                print(f"Данные: {result['data']}")
            
    except Exception as e:
        print(f"❌ Ошибка для Шахт: {e}")
        import traceback
        traceback.print_exc()
    
    # Тестируем Ростов
    print("\n\n📍 ТЕСТ 2: ПОГОДА В РОСТОВЕ")
    print("-" * 50)
    
    try:
        result = internet_system.search_internet("погода в ростове")
        print(f"✅ Результат получен: {result.get('success', False)}")
        print(f"Тип: {result.get('type', 'unknown')}")
        
        if result.get('success') and result.get('data', {}).get('sources'):
            sources = result['data']['sources']
            print(f"Найдено источников: {len(sources)}")
            
            print("\n📊 СЫРЫЕ ДАННЫЕ:")
            for i, source in enumerate(sources, 1):
                print(f"\n--- ИСТОЧНИК {i} ---")
                print(f"Заголовок: {source.get('title', 'НЕТ')}")
                print(f"URL: {source.get('url', 'НЕТ')}")
                print(f"Контент (первые 500 символов):")
                content = source.get('content', 'НЕТ КОНТЕНТА')
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-" * 40)
        else:
            print("❌ Источники не найдены")
            if result.get('error'):
                print(f"Ошибка: {result['error']}")
            if result.get('data'):
                print(f"Данные: {result['data']}")
            
    except Exception as e:
        print(f"❌ Ошибка для Ростова: {e}")
        import traceback
        traceback.print_exc()
    
    # Тестируем Ростов-на-Дону
    print("\n\n📍 ТЕСТ 3: ПОГОДА В РОСТОВЕ-НА-ДОНУ")
    print("-" * 50)
    
    try:
        result = internet_system.search_internet("погода в ростове-на-дону")
        print(f"✅ Результат получен: {result.get('success', False)}")
        print(f"Тип: {result.get('type', 'unknown')}")
        
        if result.get('success') and result.get('data', {}).get('sources'):
            sources = result['data']['sources']
            print(f"Найдено источников: {len(sources)}")
            
            print("\n📊 СЫРЫЕ ДАННЫЕ:")
            for i, source in enumerate(sources, 1):
                print(f"\n--- ИСТОЧНИК {i} ---")
                print(f"Заголовок: {source.get('title', 'НЕТ')}")
                print(f"URL: {source.get('url', 'НЕТ')}")
                print(f"Контент (первые 500 символов):")
                content = source.get('content', 'НЕТ КОНТЕНТА')
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-" * 40)
        else:
            print("❌ Источники не найдены")
            if result.get('error'):
                print(f"Ошибка: {result['error']}")
            if result.get('data'):
                print(f"Данные: {result['data']}")
            
    except Exception as e:
        print(f"❌ Ошибка для Ростова-на-Дону: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🏁 ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_weather_raw_data() 