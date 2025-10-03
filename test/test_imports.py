#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправления импортов.
Проверяет, что все модули могут быть импортированы без ошибок.
"""

import sys
from pathlib import Path

# Добавляем путь к backend
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_imports():
    """Тестирует импорт всех модулей."""
    print("🔍 Тестирование импортов...")
    
    tests = [
        ("config", "backend/config.py"),
        ("utils.import_helper", "backend/utils/import_helper.py"),
        ("api.bingx_api", "backend/api/bingx_api.py"),
        ("api.crypto_exchange_integration", "backend/api/crypto_exchange_integration.py"),
        ("api.chatumba_analyzer", "backend/api/chatumba_analyzer.py"),
    ]
    
    passed = 0
    total = len(tests)
    
    for module_name, file_path in tests:
        try:
            module = __import__(module_name, fromlist=['*'])
            print(f"✅ {module_name} - импортирован успешно")
            passed += 1
        except ImportError as e:
            print(f"❌ {module_name} - ошибка импорта: {e}")
        except Exception as e:
            print(f"⚠️ {module_name} - неожиданная ошибка: {e}")
    
    print(f"\n📊 Результаты: {passed}/{total} модулей импортированы успешно")
    
    if passed == total:
        print("🎉 Все импорты работают корректно!")
        return True
    else:
        print("⚠️ Некоторые модули не удалось импортировать")
        return False

def test_helper_functions():
    """Тестирует функции из import_helper."""
    print("\n🔧 Тестирование функций import_helper...")
    
    try:
        from utils.import_helper import get_crypto_integration, get_bingx_client, get_chatumba_analyzer
        
        # Тест get_crypto_integration
        crypto_integration = get_crypto_integration()
        if crypto_integration:
            print("✅ get_crypto_integration - работает")
        else:
            print("⚠️ get_crypto_integration - возвращает None (возможно, API ключи не настроены)")
        
        # Тест get_bingx_client
        bingx_client = get_bingx_client()
        if bingx_client:
            print("✅ get_bingx_client - работает")
        else:
            print("⚠️ get_bingx_client - возвращает None (возможно, API ключи не настроены)")
        
        # Тест get_chatumba_analyzer
        analyzer = get_chatumba_analyzer()
        if analyzer:
            print("✅ get_chatumba_analyzer - работает")
        else:
            print("⚠️ get_chatumba_analyzer - возвращает None")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании helper функций: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование исправления импортов")
    print("=" * 50)
    
    # Тестируем импорты
    imports_ok = test_imports()
    
    # Тестируем helper функции
    helper_ok = test_helper_functions()
    
    print("\n" + "=" * 50)
    if imports_ok and helper_ok:
        print("🎉 Все тесты пройдены! Импорты исправлены.")
    else:
        print("⚠️ Некоторые тесты не прошли. Проверьте настройки.")

if __name__ == "__main__":
    main() 