#!/usr/bin/env python3
"""
Упрощенный тест интеграции интернет-системы
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

def test_simple_integration():
    """Тестирование простой интеграции"""
    
    print("🔗 УПРОЩЕННЫЙ ТЕСТ ИНТЕГРАЦИИ")
    print("=" * 50)
    
    try:
        # Тестируем импорт интернет-системы
        from simple_internet_system import SimpleInternetSystem
        print("✅ Интернет-система импортирована")
        
        # Создаем экземпляр
        system = SimpleInternetSystem()
        print("✅ Экземпляр создан")
        
        # Тестируем поиск погоды
        print("\n🌤️ Тестируем поиск погоды...")
        result = system.search_internet("погода в Москве")
        
        if result.get('success'):
            data = result['data']
            print(f"✅ Поиск успешен")
            print(f"   Тип: {data.get('type', 'unknown')}")
            
            if data.get('type') == 'weather':
                print(f"   Город: {data.get('city', 'N/A')}")
                print(f"   Источники: {len(data.get('sources', []))}")
                
                # Показываем сырые данные
                for i, source in enumerate(data.get('sources', [])[:2], 1):
                    print(f"\n   --- ИСТОЧНИК {i} ---")
                    print(f"   Заголовок: {source.get('title', 'N/A')[:50]}...")
                    print(f"   URL: {source.get('url', 'N/A')}")
                    print(f"   Контент: {source.get('content', 'N/A')[:100]}...")
        else:
            print(f"❌ Поиск не удался: {result.get('error', 'Unknown error')}")
        
        # Тестируем поиск новостей
        print("\n📰 Тестируем поиск новостей...")
        news_result = system.search_internet("последние новости России")
        
        if news_result.get('success'):
            data = news_result['data']
            print(f"✅ Поиск новостей успешен")
            print(f"   Найдено новостей: {len(data)}")
            
            for i, news in enumerate(data[:2], 1):
                print(f"\n   --- НОВОСТЬ {i} ---")
                print(f"   Заголовок: {news.get('title', 'N/A')[:50]}...")
                print(f"   URL: {news.get('url', 'N/A')}")
                print(f"   Контент: {news.get('content', 'N/A')[:100]}...")
        else:
            print(f"❌ Поиск новостей не удался: {news_result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 50)
        print("✅ СЫРЫЕ ДАННЫЕ ГОТОВЫ ДЛЯ МОДЕЛИ!")
        print("💡 Теперь модель получит необработанные данные и сама извлечет нужную информацию")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_integration() 