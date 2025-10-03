#!/usr/bin/env python3
"""
Тест очистки запросов от слова "бот"
"""

import sys
import os
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

def test_query_cleaning():
    """Тестируем очистку запросов"""
    
    try:
        from ikar_internet_integration import IKARInternetIntegration
        
        print("🧪 Тестируем очистку запросов от слова 'бот'...")
        
        integration = IKARInternetIntegration()
        
        # Тестовые запросы
        test_queries = [
            "Бот, расскажи что по погоде в Шахтах на сегодня",
            "бот, какие новости?",
            "Бот, что происходит с биткоином?",
            "боту расскажи про погоду",
            "бот посмотри что нового",
            "Бот, найди информацию о криптовалютах",
            "бот, что по новостям сегодня?",
            "Бот, расскажи про погоду в Москве",
            "бот, какие последние новости?",
            "Бот, что происходит в мире?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Тестируем: '{query}'")
            
            # Очищаем запрос
            cleaned = integration._clean_search_query(query)
            print(f"   Очищенный: '{cleaned}'")
            
            # Проверяем, нужен ли интернет-поиск
            needs_search, search_query, confidence = integration.needs_internet_search(query)
            print(f"   Нужен поиск: {needs_search}")
            print(f"   Поисковый запрос: '{search_query}'")
            print(f"   Уверенность: {confidence:.2f}")
        
        print("\n🎉 Тест завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query_cleaning() 