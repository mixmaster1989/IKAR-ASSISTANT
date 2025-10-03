#!/usr/bin/env python3
"""
🧪 ТЕСТ РЕАЛЬНОГО ПАРСИНГА
Тестируем улучшенный парсинг на реальных рабочих сайтах
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from improved_content_extractor import get_extractor

async def test_real_parsing():
    """Тестирование на реальных сайтах"""
    
    print("🧪 ТЕСТ РЕАЛЬНОГО ПАРСИНГА")
    print("=" * 60)
    
    extractor = await get_extractor()
    
    # РЕАЛЬНЫЕ рабочие URL для тестирования
    real_test_cases = [
        {
            "url": "https://www.interfax.ru/russia/",
            "query": "новости россия",
            "expected_type": "news"
        },
        {
            "url": "https://habr.com/ru/",
            "query": "технологии",
            "expected_type": "blog"
        },
        {
            "url": "https://www.rbc.ru/",
            "query": "новости",
            "expected_type": "news"
        },
        {
            "url": "https://ria.ru/",
            "query": "новости сегодня",
            "expected_type": "news"
        },
        {
            "url": "https://ru.wikipedia.org/wiki/Программирование",
            "query": "программирование",
            "expected_type": "wikipedia"
        }
    ]
    
    print("📋 РЕЗУЛЬТАТЫ РЕАЛЬНОГО ПАРСИНГА:")
    print("-" * 60)
    
    successful_tests = []
    failed_tests = []
    
    for i, test_case in enumerate(real_test_cases, 1):
        print(f"\n{i}. {test_case['url']}")
        print(f"   Запрос: '{test_case['query']}'")
        print(f"   Ожидаемый тип: {test_case['expected_type']}")
        
        try:
            content = await extractor.extract_content(test_case['url'], test_case['query'])
            
            if content:
                print(f"   ✅ УСПЕХ")
                print(f"   📝 Метод: {content.extraction_method}")
                print(f"   📊 Слов: {content.word_count}")
                print(f"   🎯 Релевантность: {content.relevance_score:.2f}")
                print(f"   📰 Заголовок: {content.title[:100]}...")
                print(f"   👤 Автор: {content.author or 'Не указан'}")
                print(f"   📅 Дата: {content.publish_date or 'Не указана'}")
                print(f"   📄 Превью: {content.text[:200]}...")
                
                # Оценка качества
                quality_score = 0
                if content.word_count > 200:
                    quality_score += 1
                if content.relevance_score > 0.5:
                    quality_score += 1
                if content.title:
                    quality_score += 1
                if content.author:
                    quality_score += 1
                
                quality_text = "Отлично" if quality_score >= 3 else "Хорошо" if quality_score >= 2 else "Плохо"
                print(f"   ⭐ Качество: {quality_text} ({quality_score}/4)")
                
                successful_tests.append({
                    'url': test_case['url'],
                    'content': content,
                    'quality_score': quality_score
                })
                
            else:
                print(f"   ❌ НЕ УДАЛОСЬ ИЗВЛЕЧЬ КОНТЕНТ")
                failed_tests.append({
                    'url': test_case['url'],
                    'reason': 'No content extracted'
                })
                
        except Exception as e:
            print(f"   💥 ОШИБКА: {e}")
            failed_tests.append({
                'url': test_case['url'],
                'reason': str(e)
            })
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("📊 СТАТИСТИКА РЕАЛЬНОГО ТЕСТИРОВАНИЯ:")
    
    # Подсчитываем статистику
    total_tests = len(real_test_cases)
    successful_extractions = len(successful_tests)
    
    print(f"Всего тестов: {total_tests}")
    print(f"Успешных извлечений: {successful_extractions}")
    print(f"Процент успеха: {(successful_extractions/total_tests)*100:.1f}%")
    
    if successful_extractions > 0:
        total_words = sum(t['content'].word_count for t in successful_tests)
        total_relevance = sum(t['content'].relevance_score for t in successful_tests)
        avg_quality = sum(t['quality_score'] for t in successful_tests) / successful_extractions
        
        print(f"Среднее количество слов: {total_words/successful_extractions:.0f}")
        print(f"Средняя релевантность: {total_relevance/successful_extractions:.2f}")
        print(f"Средний балл качества: {avg_quality:.1f}/4")
        
        # Анализ методов
        methods = {}
        for test in successful_tests:
            method = test['content'].extraction_method
            methods[method] = methods.get(method, 0) + 1
        
        print(f"\n📈 АНАЛИЗ МЕТОДОВ:")
        for method, count in methods.items():
            print(f"   {method}: {count} раз")
        
        # Лучший результат
        best_test = max(successful_tests, key=lambda x: x['quality_score'])
        print(f"\n🏆 ЛУЧШИЙ РЕЗУЛЬТАТ:")
        print(f"   URL: {best_test['url']}")
        print(f"   Метод: {best_test['content'].extraction_method}")
        print(f"   Слов: {best_test['content'].word_count}")
        print(f"   Релевантность: {best_test['content'].relevance_score:.2f}")
        print(f"   Качество: {best_test['quality_score']}/4")
    
    if failed_tests:
        print(f"\n❌ НЕУДАЧНЫЕ ТЕСТЫ:")
        for test in failed_tests:
            print(f"   {test['url']}: {test['reason']}")
    
    await extractor.close()

if __name__ == "__main__":
    asyncio.run(test_real_parsing()) 