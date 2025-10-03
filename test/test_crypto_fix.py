#!/usr/bin/env python3
"""
🧪 ТЕСТ ИСПРАВЛЕНИЯ КРИПТОВАЛЮТ
Проверяем, правильно ли теперь распознаются запросы о криптовалютах
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from ikar_internet_integration import IKARInternetIntegration

async def test_crypto_fix():
    """Тестирование исправления логики криптовалют"""
    
    print("🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ КРИПТОВАЛЮТ")
    print("=" * 50)
    
    integration = IKARInternetIntegration()
    
    # Тестовые запросы о криптовалютах
    crypto_queries = [
        "Бот, посмотри в интернете, что за монета XRP?",
        "Бот! залезь в интернет и расскажи про монету >",
        "Что за монета Bitcoin?",
        "Расскажи про монету Ethereum",
        "Курс монеты BTC",
        "Цена монеты ETH",
        "Информация о монете XRP",
        "Что такое Bitcoin?",
        "Курс криптовалюты",
        "Цена биткоина"
    ]
    
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ КРИПТОВАЛЮТ:")
    print("-" * 50)
    
    for i, query in enumerate(crypto_queries, 1):
        needs_search, search_query, confidence = integration.needs_internet_search(query)
        
        status = "✅ ДА" if needs_search else "❌ НЕТ"
        print(f"{i:2d}. {status} (уверенность: {confidence:.2f})")
        print(f"    Запрос: '{query}'")
        if needs_search:
            print(f"    Поисковый запрос: '{search_query}'")
        print()
    
    print("=" * 50)
    print("📊 СТАТИСТИКА КРИПТОВАЛЮТ:")
    
    total_queries = len(crypto_queries)
    crypto_queries_detected = sum(1 for query in crypto_queries 
                                 if integration.needs_internet_search(query)[0])
    
    print(f"Всего запросов о криптовалютах: {total_queries}")
    print(f"Распознано как криптовалюты: {crypto_queries_detected}")
    print(f"Не распознано: {total_queries - crypto_queries_detected}")
    print(f"Процент распознавания: {(crypto_queries_detected/total_queries)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_crypto_fix()) 