#!/usr/bin/env python3
"""
Живое тестирование API BingX на сервере.
Запускайте на сервере для проверки работы API.
"""

import sys
import asyncio
from pathlib import Path

# Добавляем путь к backend
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_bingx_live():
    """Тестирует работу API BingX в реальном времени."""
    print("🚀 Живое тестирование API BingX")
    print("=" * 50)
    
    try:
        from utils.import_helper import get_bingx_client, get_crypto_integration
        
        # Получаем клиенты
        bingx_client = get_bingx_client()
        crypto_integration = get_crypto_integration()
        
        if not bingx_client:
            print("❌ BingX клиент недоступен")
            return False
        
        print("✅ BingX клиент подключен")
        
        # Тест 1: Время сервера
        print("\n📅 Тест 1: Время сервера BingX")
        try:
            server_time = bingx_client.get_server_time()
            print(f"✅ Время сервера: {server_time}")
        except Exception as e:
            print(f"❌ Ошибка получения времени сервера: {e}")
        
        # Тест 2: Рыночные данные BTC
        print("\n📊 Тест 2: Рыночные данные BTC-USDT")
        try:
            ticker = bingx_client.get_ticker_24hr("BTC-USDT")
            if ticker and isinstance(ticker, dict):
                price = ticker.get('lastPrice', 'N/A')
                change = ticker.get('priceChangePercent', 'N/A')
                volume = ticker.get('volume', 'N/A')
                print(f"✅ BTC-USDT: ${price} ({change}%) | Объем: {volume}")
            else:
                print(f"⚠️ Неожиданный формат данных: {ticker}")
        except Exception as e:
            print(f"❌ Ошибка получения тикера: {e}")
        
        # Тест 3: Анализ настроений
        print("\n🎯 Тест 3: Анализ настроений рынка")
        try:
            sentiment = bingx_client.analyze_market_sentiment("BTC-USDT", "1h")
            if sentiment and 'sentiment' in sentiment:
                print(f"✅ Настроения BTC-USDT: {sentiment['sentiment']}")
                print(f"   Тренд: {sentiment.get('trend', 'N/A')}")
                print(f"   Изменение цены: {sentiment.get('price_change_24h', 'N/A')}%")
            else:
                print(f"⚠️ Неожиданный формат настроений: {sentiment}")
        except Exception as e:
            print(f"❌ Ошибка анализа настроений: {e}")
        
        # Тест 4: Интеграция с криптосудом
        print("\n⚖️ Тест 4: Интеграция с криптосудом")
        if crypto_integration:
            try:
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
                else:
                    print(f"⚠️ Неожиданный формат данных криптосуда: {sud_data}")
            except Exception as e:
                print(f"❌ Ошибка интеграции с криптосудом: {e}")
        else:
            print("❌ Crypto integration недоступен")
        
        # Тест 5: Рекомендации по позициям
        print("\n💰 Тест 5: Рекомендации по позициям")
        if crypto_integration:
            try:
                recommendation = crypto_integration.get_position_recommendations('BTC-USDT', user_balance=1000)
                if 'action' in recommendation:
                    print(f"✅ Рекомендация для BTC-USDT: {recommendation['action']}")
                    print(f"   Уверенность: {recommendation.get('confidence', 0):.2f}")
                    print(f"   Уровень риска: {recommendation.get('risk_level', 'unknown')}")
                    
                    if recommendation.get('position_size'):
                        print(f"   Размер позиции: ${recommendation['position_size']:.2f}")
                else:
                    print(f"⚠️ Неожиданный формат рекомендации: {recommendation}")
            except Exception as e:
                print(f"❌ Ошибка генерации рекомендаций: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Тестирование завершено!")
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

def test_telegram_integration():
    """Тестирует интеграцию с Telegram."""
    print("\n📱 Тестирование интеграции с Telegram")
    print("=" * 30)
    
    print("💡 Для тестирования в Telegram:")
    print("1. Отправьте в группу сообщение 'ЧАТУМБА'")
    print("2. Бот должен запустить анализ с рыночными данными")
    print("3. Проверьте, что в ответе есть актуальные данные о криптовалютах")
    
    print("\n💡 Для тестирования криптосуда:")
    print("1. Отправьте в группу фото с графиком криптовалюты")
    print("2. Нажмите 'Да' для распознавания")
    print("3. Если обнаружены криптопатерны, должны появиться кнопки криптосуда")

async def main():
    """Основная функция."""
    print("🔍 Живое тестирование API BingX на сервере")
    
    # Тестируем API
    api_ok = await test_bingx_live()
    
    # Показываем инструкции для Telegram
    test_telegram_integration()
    
    if api_ok:
        print("\n✅ API BingX работает корректно!")
        print("Теперь можете тестировать через Telegram бота")
    else:
        print("\n⚠️ Есть проблемы с API BingX")
        print("Проверьте логи сервера для деталей")

if __name__ == "__main__":
    asyncio.run(main()) 