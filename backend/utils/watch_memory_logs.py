#!/usr/bin/env python3
"""
👁️ Монитор логов памяти в реальном времени
"""

import os
import time
import sys
from pathlib import Path

def watch_memory_logs():
    """Следит за логами памяти в реальном времени"""
    log_file = Path("logs/memory_debug.log")
    
    if not log_file.exists():
        print("❌ Файл логов не найден: logs/memory_debug.log")
        print("💡 Сначала включите логирование: python3 backend/utils/enable_memory_debug.py")
        return
    
    print("🧠 Мониторинг логов памяти в реальном времени...")
    print("📝 Файл: logs/memory_debug.log")
    print("⏹️  Нажмите Ctrl+C для остановки")
    print("=" * 80)
    
    # Читаем последние 50 строк
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                print("".join(lines[-50:]))
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
    
    # Следим за изменениями
    last_size = log_file.stat().st_size
    
    try:
        while True:
            time.sleep(0.5)
            current_size = log_file.stat().st_size
            
            if current_size > last_size:
                with open(log_file, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_content = f.read()
                    if new_content:
                        print(new_content, end='')
                last_size = current_size
                
    except KeyboardInterrupt:
        print("\n\n🛑 Мониторинг остановлен")

if __name__ == "__main__":
    watch_memory_logs()