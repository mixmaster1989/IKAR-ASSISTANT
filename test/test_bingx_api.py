#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы API BingX.
Запускайте только после настройки переменных окружения.
"""

import os
import sys
from pathlib import Path

# Добавляем путь к backend
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from api.bingx_api import bingx_client
    from api.crypto_exchange_integration import crypto_integration
    from config import BINGX_API_KEY, BINGX_SECRET_KEY
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что вы находитесь в корневой папке проекта")
    sys.exit(1)

def test_bingx_connection():
    """Тестирует подключение к API BingX."""
    print("🔗 Тестирование подключения к BingX API...")
    
    if not BINGX_API_KEY or not BINGX_SECRET_KEY:
        print("❌ API ключи BingX не настроены!")
        print("Добавьте BINGX_API_KEY и BINGX_SECRET_KEY в файл .env")
        return False
    
    try:
        # Тест получения времени сервера
        server_time = bingx_client.get_server_time()
        print(f"✅ Время сервера BingX: {server_time}")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к BingX API: {e}")
        return False

def test_market_data():
    """Тестирует получение рыночных данных."""
    print("\n📊 Тестирование получения рыночных данных...")
    
    try:
        # Тест получения информации о бирже
        exchange_info = bingx_client.get_exchange_info()
        print(f"✅ Информация о бирже получена")
        
        # Тест получения тикера BTC-USDT
        ticker = bingx_client.get_ticker_24hr("BTC-USDT")
        if ticker and isinstance(ticker, dict):
            print(f"✅ Тикер BTC-USDT: ${ticker.get('lastPrice', 'N/A')}")
        else:
            print("⚠️ Не удалось получить тикер BTC-USDT")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка получения рыночных данных: {e}")
        return False

def test_crypto_integration():
    """Тестирует интеграцию с системой криптосуда."""
    print("\n🎯 Тестирование интеграции с криптосудом...")
    
    try:
        # Тест получения данных для криптосуда
        sud_data = crypto_integration.get_crypto_sud_data(['BTC-USDT', 'ETH-USDT'])
        
        if 'symbols' in sud_data:
            print(f"✅ Данные для криптосуда получены: {len(sud_data['symbols'])} символов")
            
            # Показываем трендовые пары
            trending_pairs = sud_data.get('trending_pairs', [])
            if trending_pairs:
                print("📈 Трендовые пары:")
                for pair in trending_pairs[:3]:
                    print(f"   - {pair['symbol']}: {pair['sentiment']} ({pair['price_change']:.2f}%)")
            
            # Показываем оценку риска
            risk_assessment = sud_data.get('risk_assessment', {})
            print(f"⚠️ Оценка риска: {risk_assessment.get('overall_risk', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка интеграции с криптосудом: {e}")
        return False

def test_position_recommendations():
    """Тестирует генерацию рекомендаций по позициям."""
    print("\n💰 Тестирование рекомендаций по позициям...")
    
    try:
        # Тест рекомендаций для BTC-USDT
        recommendation = crypto_integration.get_position_recommendations('BTC-USDT', user_balance=1000)
        
        if 'action' in recommendation:
            print(f"✅ Рекомендация для BTC-USDT: {recommendation['action']}")
            print(f"   Уверенность: {recommendation.get('confidence', 0):.2f}")
            print(f"   Уровень риска: {recommendation.get('risk_level', 'unknown')}")
            
            if recommendation.get('position_size'):
                print(f"   Размер позиции: ${recommendation['position_size']:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка генерации рекомендаций: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование интеграции с API BingX")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print(f"🔑 API Key: {'✅ Настроен' if BINGX_API_KEY else '❌ Не настроен'}")
    print(f"🔑 Secret Key: {'✅ Настроен' if BINGX_SECRET_KEY else '❌ Не настроен'}")
    
    if not BINGX_API_KEY or not BINGX_SECRET_KEY:
        print("\n❌ Для тестирования необходимо настроить API ключи BingX")
        print("См. файл BINGX_SETUP.md для инструкций")
        return
    
    # Запускаем тесты
    tests = [
        test_bingx_connection,
        test_market_data,
        test_crypto_integration,
        test_position_recommendations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Неожиданная ошибка в тесте {test.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно! Интеграция с BingX работает корректно.")
    else:
        print("⚠️ Некоторые тесты не прошли. Проверьте настройки и подключение к интернету.")

if __name__ == "__main__":
    main() 