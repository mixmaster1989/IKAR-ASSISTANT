#!/usr/bin/env python3
"""
🧪 Тест импорта debug логгера
"""

def test_import():
    print("🔧 Тестируем импорт debug логгера...")
    
    try:
        import sys
        import os
        print(f"📁 Текущая директория: {os.getcwd()}")
        print(f"🐍 Python path: {sys.path[:3]}...")
        
        # Тест 1: Прямой импорт
        try:
            from backend.utils.memory_debug_logger import get_memory_debug_logger
            logger = get_memory_debug_logger()
            print("✅ Прямой импорт: успешно")
            logger.start_request("test", "test", "test message")
            print("✅ Логгер работает!")
            return True
        except Exception as e:
            print(f"❌ Прямой импорт: {e}")
        
        # Тест 2: Относительный импорт
        try:
            sys.path.append('backend')
            from utils.memory_debug_logger import get_memory_debug_logger
            logger = get_memory_debug_logger()
            print("✅ Относительный импорт: успешно")
            return True
        except Exception as e:
            print(f"❌ Относительный импорт: {e}")
        
        # Тест 3: Полный путь
        try:
            backend_path = os.path.join(os.getcwd(), 'backend')
            sys.path.insert(0, backend_path)
            from utils.memory_debug_logger import get_memory_debug_logger
            logger = get_memory_debug_logger()
            print("✅ Полный путь: успешно")
            return True
        except Exception as e:
            print(f"❌ Полный путь: {e}")
            
        return False
        
    except Exception as e:
        print(f"💥 Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    if test_import():
        print("\n🎉 Импорт логгера работает!")
    else:
        print("\n💔 Импорт логгера не работает")