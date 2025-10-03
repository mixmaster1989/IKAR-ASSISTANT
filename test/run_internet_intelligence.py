#!/usr/bin/env python3
"""
🚀 БЫСТРЫЙ ЗАПУСК СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА IKAR
Демонстрация и тестирование революционной системы
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_internet_intelligence():
    """Демонстрация системы интернет-интеллекта"""
    print("🌐 ДЕМОНСТРАЦИЯ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА IKAR")
    print("=" * 80)
    
    try:
        # Импортируем компоненты
        from internet_intelligence_system import InternetIntelligenceSystem
        from ikar_internet_integration import IKARInternetIntegration
        from integrate_with_ikar import enhance_ikar_message
        
        print("✅ Компоненты загружены успешно")
        
        # Демонстрация 1: Поиск в интернете
        print("\n🔍 ДЕМО 1: Поиск в интернете")
        print("-" * 40)
        
        system = InternetIntelligenceSystem()
        
        query = "последние новости о развитии искусственного интеллекта"
        print(f"Поиск: '{query}'")
        
        results = await system.search_internet(query, max_total_results=5)
        print(f"✅ Найдено {len(results)} результатов")
        
        if results:
            # Извлекаем контент
            results_with_content = await system.extract_content(results[:3])
            
            # AI обработка
            processed_info = await system.process_with_ai(query, results_with_content)
            
            print(f"📊 Результаты обработки:")
            print(f"   Уверенность: {processed_info.confidence_score:.2f}")
            print(f"   Ключевых моментов: {len(processed_info.key_points)}")
            print(f"   Источников: {len(processed_info.sources)}")
            print(f"   Время обработки: {processed_info.processing_time:.2f}с")
            
            print(f"\n🧠 AI-ВЫЖИМКА:")
            print(processed_info.ai_summary[:300] + "...")
            
            print(f"\n🔑 КЛЮЧЕВЫЕ МОМЕНТЫ:")
            for i, point in enumerate(processed_info.key_points[:3], 1):
                print(f"{i}. {point}")
        
        await system.close()
        
        # Демонстрация 2: Интеграция с IKAR
        print("\n🤖 ДЕМО 2: Интеграция с IKAR")
        print("-" * 40)
        
        test_cases = [
            {
                "query": "Как дела?",
                "response": "У меня все хорошо, спасибо!",
                "description": "Обычный запрос (без улучшения)"
            },
            {
                "query": "Какие последние новости о технологиях?",
                "response": "Технологии активно развиваются в современном мире.",
                "description": "Запрос новостей (с улучшением)"
            },
            {
                "query": "Что происходит с Bitcoin сегодня?",
                "response": "Bitcoin - это криптовалюта, но для актуальных данных нужна свежая информация.",
                "description": "Крипто-запрос (с улучшением)"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n📝 Тест {i}: {case['description']}")
            print(f"Запрос: '{case['query']}'")
            print(f"Оригинальный ответ: '{case['response']}'")
            
            enhanced = await enhance_ikar_message(case['query'], case['response'], f"demo_user_{i}")
            
            improvement_ratio = len(enhanced) / len(case['response'])
            print(f"Улучшенный ответ ({improvement_ratio:.2f}x):")
            print(f"'{enhanced[:200]}{'...' if len(enhanced) > 200 else ''}'")
        
        # Демонстрация 3: Анализ запросов
        print("\n🔬 ДЕМО 3: Анализ запросов")
        print("-" * 40)
        
        integration = IKARInternetIntegration()
        
        test_queries = [
            "Как дела?",
            "Последние новости",
            "Расскажи анекдот",
            "Что происходит с криптовалютами?",
            "Погода сегодня"
        ]
        
        for query in test_queries:
            needs_search, search_query, confidence = integration.needs_internet_search(query)
            status = "🌐 НУЖЕН" if needs_search else "❌ НЕ НУЖЕН"
            print(f"'{query}' -> {status} (уверенность: {confidence:.2f})")
        
        await integration.close()
        
        print("\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка демонстрации: {e}")
        print(f"❌ Ошибка: {e}")

async def quick_test():
    """Быстрый тест системы"""
    print("⚡ БЫСТРЫЙ ТЕСТ СИСТЕМЫ")
    print("=" * 40)
    
    try:
        from integrate_with_ikar import enhance_ikar_message
        
        # Простой тест
        user_query = "последние новости о технологиях"
        bot_response = "Технологии развиваются."
        
        print(f"Тестируем: '{user_query}'")
        
        enhanced = await enhance_ikar_message(user_query, bot_response, "quick_test")
        
        improvement = len(enhanced) / len(bot_response)
        print(f"✅ Тест пройден! Улучшение: {improvement:.2f}x")
        
        return True
        
    except Exception as e:
        print(f"❌ Тест не пройден: {e}")
        return False

async def start_web_interface():
    """Запуск веб-интерфейса"""
    print("🌐 ЗАПУСК ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 40)
    
    try:
        from flask import Flask
        from internet_api import register_internet_api
        
        app = Flask(__name__)
        register_internet_api(app)
        
        print("✅ Веб-интерфейс запущен")
        print("📱 Откройте: http://localhost:6667")
        print("🔧 Интернет-интеллект: http://localhost:6666/internet-intelligence.html")
        
        # Запускаем в фоне
        import threading
        
        def run_flask():
            app.run(host='0.0.0.0', port=6667, debug=False)
        
        thread = threading.Thread(target=run_flask, daemon=True)
        thread.start()
        
        print("✅ Веб-сервер запущен в фоновом режиме")
        
    except Exception as e:
        print(f"❌ Ошибка запуска веб-интерфейса: {e}")

def show_menu():
    """Показать меню опций"""
    print("\n🎮 МЕНЮ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА")
    print("=" * 50)
    print("1. 🚀 Полная демонстрация")
    print("2. ⚡ Быстрый тест")
    print("3. 🌐 Запуск веб-интерфейса")
    print("4. 🧪 Запуск комплексных тестов")
    print("5. 📊 Показать статус системы")
    print("6. 🔧 Настройка системы")
    print("0. ❌ Выход")
    print("-" * 50)

async def show_system_status():
    """Показать статус системы"""
    print("📊 СТАТУС СИСТЕМЫ")
    print("=" * 30)
    
    try:
        from integrate_with_ikar import get_internet_enhancement_status
        
        status = await get_internet_enhancement_status()
        
        print(f"Статус: {status.get('status', 'unknown')}")
        print(f"Включена: {status.get('enabled', False)}")
        print(f"Автоопределение: {status.get('auto_detect', False)}")
        print(f"Порог уверенности: {status.get('confidence_threshold', 0.0)}")
        
        if 'stats' in status:
            stats = status['stats']
            print(f"Всего поисков: {stats.get('total_searches', 0)}")
            print(f"Успешных улучшений: {stats.get('successful_enhancements', 0)}")
            print(f"Средняя уверенность: {stats.get('average_confidence', 0.0):.2f}")
        
    except Exception as e:
        print(f"❌ Ошибка получения статуса: {e}")

async def configure_system():
    """Настройка системы"""
    print("🔧 НАСТРОЙКА СИСТЕМЫ")
    print("=" * 30)
    
    try:
        from integrate_with_ikar import configure_internet_enhancement
        
        print("Текущие настройки:")
        print("1. Включить/выключить систему")
        print("2. Настроить автоопределение")
        print("3. Установить порог уверенности")
        print("4. Настройки по умолчанию")
        
        choice = input("Выберите опцию (1-4): ").strip()
        
        if choice == "1":
            enabled = input("Включить систему? (y/n): ").lower() == 'y'
            configure_internet_enhancement(enabled=enabled)
            print(f"✅ Система {'включена' if enabled else 'выключена'}")
            
        elif choice == "2":
            auto_detect = input("Включить автоопределение? (y/n): ").lower() == 'y'
            configure_internet_enhancement(auto_detect=auto_detect)
            print(f"✅ Автоопределение {'включено' if auto_detect else 'выключено'}")
            
        elif choice == "3":
            try:
                threshold = float(input("Порог уверенности (0.0-1.0): "))
                configure_internet_enhancement(confidence_threshold=threshold)
                print(f"✅ Порог уверенности установлен: {threshold}")
            except ValueError:
                print("❌ Неверное значение")
                
        elif choice == "4":
            configure_internet_enhancement(
                enabled=True,
                auto_detect=True,
                confidence_threshold=0.3
            )
            print("✅ Настройки по умолчанию применены")
            
    except Exception as e:
        print(f"❌ Ошибка настройки: {e}")

async def main():
    """Главная функция"""
    print("🌐 СИСТЕМА ИНТЕРНЕТ-ИНТЕЛЛЕКТА IKAR")
    print("Революционная система автономного поиска и обработки информации")
    print("=" * 80)
    
    while True:
        show_menu()
        
        choice = input("\nВыберите опцию: ").strip()
        
        if choice == "1":
            await demo_internet_intelligence()
            
        elif choice == "2":
            await quick_test()
            
        elif choice == "3":
            await start_web_interface()
            
        elif choice == "4":
            print("🧪 Запуск комплексных тестов...")
            try:
                from test_internet_intelligence import InternetIntelligenceTester
                tester = InternetIntelligenceTester()
                await tester.run_all_tests()
            except Exception as e:
                print(f"❌ Ошибка тестирования: {e}")
                
        elif choice == "5":
            await show_system_status()
            
        elif choice == "6":
            await configure_system()
            
        elif choice == "0":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
        
        input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка: {e}") 