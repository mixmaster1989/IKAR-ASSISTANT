#!/usr/bin/env python3
"""
Быстрое тестирование API BingX с таймаутами.
"""

import sys
import asyncio
import time
from pathlib import Path

# Добавляем путь к backend
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_bingx_quick():
    """Быстрое тестирование API BingX."""
    print("🚀 Быстрое тестирование API BingX")
    print("=" * 40)
    
    try:
        from utils.import_helper import get_bingx_client
        
        # Получаем клиент
        bingx_client = get_bingx_client()
        
        if not bingx_client:
            print("❌ BingX клиент недоступен")
            return False
        
        print("✅ BingX клиент подключен")
        
        # Тест 1: Быстрая проверка статуса
        print("\n📡 Тест 1: Проверка статуса API")
        start_time = time.time()
        
        try:
            # Устанавливаем таймаут для запроса
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # Создаем сессию с таймаутами
            session = requests.Session()
            retry = Retry(connect=1, backoff_factor=0.1)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            # Тестируем базовый endpoint
            response = session.get('https://open-api.bingx.com/openApi/spot/v1/common/serverTime', 
                                 timeout=5)
            
            if response.status_code == 200:
                print("✅ API BingX доступен")
                data = response.json()
                print(f"   Статус: {data.get('code', 'unknown')}")
            else:
                print(f"⚠️ API вернул статус: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("❌ Таймаут при подключении к API")
        except requests.exceptions.ConnectionError:
            print("❌ Ошибка подключения к API")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        elapsed = time.time() - start_time
        print(f"   Время выполнения: {elapsed:.2f}с")
        
        # Тест 2: Проверка конфигурации
        print("\n⚙️ Тест 2: Проверка конфигурации")
        try:
            from config import BINGX_API_KEY, BINGX_SECRET_KEY
            
            if BINGX_API_KEY and BINGX_SECRET_KEY:
                print("✅ API ключи настроены")
                print(f"   API Key: ...{BINGX_API_KEY[-8:] if len(BINGX_API_KEY) > 8 else BINGX_API_KEY}")
                print(f"   Secret Key: ...{BINGX_SECRET_KEY[-8:] if len(BINGX_SECRET_KEY) > 8 else BINGX_SECRET_KEY}")
            else:
                print("⚠️ API ключи не настроены")
                print("   Добавьте BINGX_API_KEY и BINGX_SECRET_KEY в .env")
        except Exception as e:
            print(f"❌ Ошибка проверки конфигурации: {e}")
        
        # Тест 3: Проверка интеграции с криптосудом
        print("\n🔗 Тест 3: Проверка интеграции")
        try:
            from utils.import_helper import get_crypto_integration
            crypto_integration = get_crypto_integration()
            
            if crypto_integration:
                print("✅ Crypto integration доступен")
            else:
                print("⚠️ Crypto integration недоступен")
        except Exception as e:
            print(f"❌ Ошибка проверки интеграции: {e}")
        
        print("\n" + "=" * 40)
        print("🎉 Быстрое тестирование завершено!")
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

def test_telegram_integration():
    """Инструкции по тестированию в Telegram."""
    print("\n📱 Инструкции по тестированию в Telegram")
    print("=" * 40)
    
    print("💡 Для тестирования ЧАТУМБА:")
    print("1. Отправьте в группу: 'ЧАТУМБА'")
    print("2. Бот должен проанализировать группу")
    print("3. В ответе должны быть рыночные данные")
    
    print("\n💡 Для тестирования криптосуда:")
    print("1. Отправьте фото с графиком криптовалюты")
    print("2. Нажмите 'Да' для распознавания")
    print("3. Если найдены криптопатерны → кнопки криптосуда")
    print("4. Нажмите 'Да' для запуска криптосуда")
    print("5. Проверьте, что в анализе есть данные BingX API")

def main():
    """Основная функция."""
    print("🔍 Быстрое тестирование API BingX")
    
    # Быстрое тестирование
    success = test_bingx_quick()
    
    # Инструкции
    test_telegram_integration()
    
    if success:
        print("\n✅ Система готова к тестированию!")
        print("Запустите сервер и протестируйте через Telegram")
    else:
        print("\n⚠️ Есть проблемы с настройкой")
        print("Проверьте конфигурацию и логи")

if __name__ == "__main__":
    main() 