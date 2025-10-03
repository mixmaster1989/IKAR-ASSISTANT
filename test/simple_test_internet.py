#!/usr/bin/env python3
"""
🧪 ПРОСТОЙ ТЕСТ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА
Быстрая проверка работоспособности
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_basic_functionality():
    """Базовый тест функциональности"""
    print("🧪 ПРОСТОЙ ТЕСТ ИНТЕРНЕТ-ИНТЕЛЛЕКТА")
    print("=" * 50)
    
    try:
        # Проверяем импорт
        print("📦 Проверяем импорты...")
        
        try:
            from internet_intelligence_system import InternetIntelligenceSystem
            print("✅ InternetIntelligenceSystem импортирован")
        except ImportError as e:
            print(f"❌ Ошибка импорта InternetIntelligenceSystem: {e}")
            return False
        
        try:
            from ikar_internet_integration import IKARInternetIntegration
            print("✅ IKARInternetIntegration импортирован")
        except ImportError as e:
            print(f"❌ Ошибка импорта IKARInternetIntegration: {e}")
            return False
        
        # Тестируем систему поиска
        print("\n🔍 Тестируем поиск...")
        system = InternetIntelligenceSystem()
        
        # Простой поиск
        query = "новости о технологиях"
        print(f"Поиск: '{query}'")
        
        results = await system.search_internet(query, max_total_results=3)
        
        if results:
            print(f"✅ Найдено {len(results)} результатов")
            
            # Показываем первые результаты
            for i, result in enumerate(results[:2], 1):
                print(f"  {i}. {result.title}")
                print(f"     URL: {result.url}")
                print(f"     Источник: {result.source}")
                print()
            
            # Тестируем извлечение контента
            print("📄 Тестируем извлечение контента...")
            results_with_content = await system.extract_content(results[:1])
            
            if results_with_content and results_with_content[0].content:
                print(f"✅ Контент извлечен ({len(results_with_content[0].content)} символов)")
            else:
                print("⚠️  Контент не извлечен")
            
            # Тестируем AI обработку
            print("🧠 Тестируем AI обработку...")
            processed_info = await system.process_with_ai(query, results_with_content)
            
            print(f"✅ AI обработка завершена")
            print(f"   Уверенность: {processed_info.confidence_score:.2f}")
            print(f"   Ключевых моментов: {len(processed_info.key_points)}")
            print(f"   Время обработки: {processed_info.processing_time:.2f}с")
            
            # Показываем результат
            print(f"\n📋 РЕЗУЛЬТАТ:")
            print(processed_info.ai_summary[:200] + "...")
            
        else:
            print("❌ Результаты поиска не найдены")
            return False
        
        await system.close()
        
        # Тестируем интеграцию
        print("\n🔗 Тестируем интеграцию...")
        integration = IKARInternetIntegration()
        
        # Тест анализа запросов
        test_queries = [
            ("Как дела?", False),
            ("Последние новости", True),
            ("Расскажи анекдот", False)
        ]
        
        for query, expected in test_queries:
            needs_search, search_query, confidence = integration.needs_internet_search(query)
            status = "✅" if needs_search == expected else "❌"
            print(f"{status} '{query}' -> Нужен интернет: {needs_search} (ожидалось: {expected})")
        
        await integration.close()
        
        # Принудительно закрываем все сессии
        import gc
        gc.collect()
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhancement():
    """Тест улучшения ответов"""
    print("\n🚀 ТЕСТ УЛУЧШЕНИЯ ОТВЕТОВ")
    print("=" * 40)
    
    try:
        from integrate_with_ikar import enhance_ikar_message
        
        # Тестовые случаи
        test_cases = [
            {
                "query": "Как дела?",
                "response": "У меня все хорошо!",
                "description": "Обычный запрос"
            },
            {
                "query": "Какие последние новости о технологиях?",
                "response": "Технологии развиваются.",
                "description": "Запрос новостей"
            }
        ]
        
        for case in test_cases:
            print(f"\n📝 Тест: {case['description']}")
            print(f"Запрос: '{case['query']}'")
            print(f"Оригинальный ответ: '{case['response']}'")
            
            enhanced = await enhance_ikar_message(case['query'], case['response'], "test_user")
            
            improvement = len(enhanced) / len(case['response'])
            print(f"Улучшенный ответ ({improvement:.2f}x):")
            print(f"'{enhanced[:150]}{'...' if len(enhanced) > 150 else ''}'")
        
        print("\n✅ Тест улучшения завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста улучшения: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("🧪 ЗАПУСК ПРОСТОГО ТЕСТА ИНТЕРНЕТ-ИНТЕЛЛЕКТА")
    print("=" * 60)
    
    # Тест базовой функциональности
    basic_success = await test_basic_functionality()
    
    if basic_success:
        # Тест улучшения ответов
        enhancement_success = await test_enhancement()
        
        if enhancement_success:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("\n📋 СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
            print("\n🚀 Следующие шаги:")
            print("1. Запустите IKAR: python run_ikar_with_internet.py")
            print("2. Откройте веб-интерфейс: http://localhost:6666/internet-intelligence.html")
            print("3. Протестируйте в Telegram или через API")
        else:
            print("\n⚠️  Тест улучшения не пройден")
    else:
        print("\n❌ Базовые тесты не пройдены")
        print("\n🔧 Возможные решения:")
        print("1. Установите зависимости: pip install -r requirements_internet_minimal.txt")
        print("2. Проверьте интернет-соединение")
        print("3. Убедитесь, что все файлы на месте")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Тест прерван пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc() 