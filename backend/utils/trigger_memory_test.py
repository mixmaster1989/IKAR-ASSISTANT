#!/usr/bin/env python3
"""
🧪 Тест системы логирования памяти
"""

import sys
sys.path.append('backend')

def test_memory_logging():
    """Тестируем работу системы логирования памяти"""
    
    print("🧠 Тестируем систему логирования памяти...")
    
    try:
        # Тест импорта и работы логгера
        from utils.memory_debug_logger import get_memory_debug_logger
        
        logger = get_memory_debug_logger()
        print("✅ Логгер импортирован успешно")
        
        # Симулируем обработку запроса
        request_id = logger.start_request("test_user", "test_chat", "тестовое сообщение для проверки памяти")
        print(f"✅ Запрос начат: {request_id}")
        
        logger.log_trigger_bot("test_trigger", {
            "user_id": "test_user",
            "message_length": 50,
            "test": True
        })
        print("✅ Триггер залогирован")
        
        logger.log_lazy_memory_start("test_user", "тестовый запрос")
        logger.log_lazy_memory_keywords(["тестовый", "запрос"])
        logger.log_lazy_memory_results(2, [
            {"content": "тестовое воспоминание 1", "timestamp": "2025-08-02"},
            {"content": "тестовое воспоминание 2", "timestamp": "2025-08-01"}
        ])
        print("✅ Lazy Memory залогирована")
        
        logger.log_memory_injector_start("тестовый промпт", "контекст", "test_user")
        logger.log_memory_injection_result(100, 200, 2)
        print("✅ Memory Injector залогирован")
        
        logger.end_request(True)
        print("✅ Запрос завершен")
        
        print("\n🎉 Все тесты пройдены! Проверьте logs/memory_debug.log")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_memory_logging()