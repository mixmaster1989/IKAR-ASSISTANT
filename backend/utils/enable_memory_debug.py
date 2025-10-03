#!/usr/bin/env python3
"""
🧠 Скрипт для включения отладочного логирования памяти
Запустите этот скрипт для включения детального логирования всех операций с памятью
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.memory_debug_logger import enable_memory_debug_logging

def main():
    logger = enable_memory_debug_logging()
    print("🔧 Детальное логирование памяти ВКЛЮЧЕНО")
    print(f"📝 Логи записываются в: logs/memory_debug.log")
    print("🧠 Теперь все операции с памятью будут подробно логироваться")
    print("\n💡 Отправьте запрос боту и проверьте логи!")

if __name__ == "__main__":
    main()