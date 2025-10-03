#!/usr/bin/env python3
"""
🧪 ТЕСТ ЛОГИКИ ОПРЕДЕЛЕНИЯ ИНТЕРНЕТ-ПОИСКА
Проверяем, правильно ли система определяет необходимость интернет-поиска для различных запросов
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from ikar_internet_integration import IKARInternetIntegration

async def test_internet_detection():
    """Тестирование логики определения необходимости интернет-поиска"""
    
    print("🧪 ТЕСТИРОВАНИЕ ЛОГИКИ ИНТЕРНЕТ-ПОИСКА")
    print("=" * 50)
    
    integration = IKARInternetIntegration()
    
    # Тестовые запросы
    test_queries = [
        # Запросы из логов пользователя
        "Бот, что с ираном происходит сейчас?",
        "БОТ, что по новостям сегодня?",
        "Бот, посмотри в интернете, что за монета XRP?",
        "Бот! залезь в интернет и расскажи про монету >",
        
        # Дополнительные тестовые запросы
        "Что происходит в мире сегодня?",
        "Какие новости?",
        "Что нового?",
        "Что происходит с Россией?",
        "Как дела с Украиной?",
        "Что творится в мире?",
        "Актуальные новости",
        "Что происходит сейчас?",
        "Последние события",
        "Что интересного?",
        
        # Запросы, которые НЕ должны требовать интернет
        "Привет, как дела?",
        "Расскажи анекдот",
        "Какой сегодня день недели?",
        "Сколько будет 2+2?",
        "Что такое любовь?",
    ]
    
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("-" * 50)
    
    for i, query in enumerate(test_queries, 1):
        needs_search, search_query, confidence = integration.needs_internet_search(query)
        
        status = "✅ ДА" if needs_search else "❌ НЕТ"
        print(f"{i:2d}. {status} (уверенность: {confidence:.2f})")
        print(f"    Запрос: '{query}'")
        if needs_search:
            print(f"    Поисковый запрос: '{search_query}'")
        print()
    
    print("=" * 50)
    print("📊 СТАТИСТИКА:")
    
    total_queries = len(test_queries)
    internet_queries = sum(1 for query in test_queries 
                          if integration.needs_internet_search(query)[0])
    
    print(f"Всего запросов: {total_queries}")
    print(f"Требуют интернет: {internet_queries}")
    print(f"Не требуют интернет: {total_queries - internet_queries}")
    print(f"Процент интернет-запросов: {(internet_queries/total_queries)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_internet_detection()) 