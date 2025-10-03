#!/usr/bin/env python3
"""
Тест запуска системы IKAR
"""

import sys
import os
import traceback

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Тест импортов"""
    print("🔍 Тестирование импортов...")
    
    try:
        print("  ✓ Импорт config...")
        from config import Config
        
        print("  ✓ Импорт core.personality...")
        from core.personality import ChatumbaPersonality
        
        print("  ✓ Импорт core.soul...")
        from core.soul import Soul
        
        print("  ✓ Импорт core.collective_mind...")
        from core.collective_mind import CollectiveMind
        
        print("  ✓ Импорт api.routes...")
        from api.routes import router
        
        print("✅ Все импорты успешны!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📋 Подробности:")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Тест базовой функциональности"""
    print("\n🔍 Тестирование базовой функциональности...")
    
    try:
        from config import Config
        from core.personality import ChatumbaPersonality
        
        # Создаем конфигурацию
        config = Config()
        print("  ✓ Конфигурация создана")
        
        # Создаем личность
        personality = ChatumbaPersonality("test_user")
        print("  ✓ Личность создана")
        
        # Тестируем выбор реакции
        reaction = personality.choose_reaction_type("Привет!")
        print(f"  ✓ Реакция выбрана: {reaction}")
        
        print("✅ Базовая функциональность работает!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка функциональности: {e}")
        print("📋 Подробности:")
        traceback.print_exc()
        return False

def test_fastapi_startup():
    """Тест запуска FastAPI"""
    print("\n🔍 Тестирование FastAPI...")
    
    try:
        print("  ✓ Импорт main...")
        from main import app
        
        print("  ✓ FastAPI app создан")
        print(f"  ✓ Заголовок: {app.title}")
        print(f"  ✓ Версия: {app.version}")
        
        print("✅ FastAPI готов к запуску!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка FastAPI: {e}")
        print("📋 Подробности:")
        traceback.print_exc()
        return False

def main():
    """Основная функция теста"""
    print("🚀 ТЕСТ ЗАПУСКА СИСТЕМЫ IKAR")
    print("=" * 40)
    
    # Тест импортов
    imports_ok = test_imports()
    
    # Тест функциональности
    functionality_ok = test_basic_functionality()
    
    # Тест FastAPI
    fastapi_ok = test_fastapi_startup()
    
    print("\n" + "=" * 40)
    if imports_ok and functionality_ok and fastapi_ok:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("🚀 Система готова к запуску!")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ!")
        print("🔧 Требуется дополнительная настройка")
        
        if not imports_ok:
            print("  - Проблемы с импортами")
        if not functionality_ok:
            print("  - Проблемы с функциональностью")
        if not fastapi_ok:
            print("  - Проблемы с FastAPI")

if __name__ == "__main__":
    main() 