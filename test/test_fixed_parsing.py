#!/usr/bin/env python3
"""
🧪 ТЕСТ ИСПРАВЛЕННОГО ПАРСИНГА
"""

import asyncio
import logging
from improved_content_extractor_fixed import FixedContentExtractor

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fixed_parsing():
    """Тестируем исправленный парсинг"""
    print("🧪 ТЕСТ ИСПРАВЛЕННОГО ПАРСИНГА")
    print("=" * 50)
    
    # Создаем экстрактор
    extractor = FixedContentExtractor()
    
    # Тестовые URL
    test_urls = [
        "https://www.rbc.ru/",
        "https://ria.ru/",
        "https://tass.ru/",
        "https://www.interfax.ru/"
    ]
    
    test_query = "новости сегодня"
    
    print(f"🔍 Тестируем парсинг с запросом: '{test_query}'")
    print()
    
    for i, url in enumerate(test_urls, 1):
        print(f"📄 Тест {i}: {url}")
        
        try:
            content = await extractor.extract_content(url, test_query)
            
            if content:
                print(f"   ✅ УСПЕХ!")
                print(f"   📝 Метод: {content.extraction_method}")
                print(f"   📊 Слов: {content.word_count}")
                print(f"   🎯 Релевантность: {content.relevance_score:.2f}")
                print(f"   📰 Заголовок: {content.title[:100]}...")
                print(f"   📄 Текст: {content.text[:200]}...")
            else:
                print(f"   ❌ НЕ УДАЛОСЬ ИЗВЛЕЧЬ КОНТЕНТ")
                
        except Exception as e:
            print(f"   💥 ОШИБКА: {e}")
        
        print()
    
    # Закрываем экстрактор
    await extractor.close()
    
    print("✅ ТЕСТ ЗАВЕРШЕН")

async def test_internet_system():
    """Тестируем полную систему интернет-интеллекта"""
    print("🌐 ТЕСТ ПОЛНОЙ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА")
    print("=" * 50)
    
    try:
        from internet_intelligence_system import InternetIntelligenceSystem
        
        # Создаем систему
        system = InternetIntelligenceSystem()
        
        # Тестовый запрос
        test_query = "последние новости сегодня"
        
        print(f"🔍 Запрос: '{test_query}'")
        print()
        
        # Получаем интернет-информацию
        result = await system.get_internet_intelligence(test_query)
        
        print(f"✅ РЕЗУЛЬТАТ:")
        print(f"   📊 Уверенность: {result.confidence_score:.2f}")
        print(f"   ⏱️  Время обработки: {result.processing_time:.2f}с")
        print(f"   📰 Источники: {len(result.sources)}")
        print(f"   🧠 AI-выжимка: {result.ai_summary[:300]}...")
        print(f"   🔑 Ключевые моменты:")
        for i, point in enumerate(result.key_points[:5], 1):
            print(f"      {i}. {point}")
        
        # Закрываем систему
        await system.close()
        
    except Exception as e:
        print(f"💥 ОШИБКА СИСТЕМЫ: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТОВ ИСПРАВЛЕННОГО ПАРСИНГА")
    print("=" * 60)
    
    # Тест 1: Исправленный экстрактор
    await test_fixed_parsing()
    
    print("\n" + "=" * 60)
    
    # Тест 2: Полная система
    await test_internet_system()
    
    print("\n🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")

if __name__ == "__main__":
    asyncio.run(main()) 