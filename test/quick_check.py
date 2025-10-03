#!/usr/bin/env python3
"""
Быстрая проверка статуса системы IKAR
"""

import subprocess
import sys
from pathlib import Path

def check_service_status():
    """Проверка статуса сервиса"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'chatumba'], 
                              capture_output=True, text=True)
        status = result.stdout.strip()
        
        if status == 'active':
            print("✅ Сервис chatumba АКТИВЕН")
            return True
        else:
            print(f"❌ Сервис chatumba НЕ АКТИВЕН: {status}")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки сервиса: {e}")
        return False

def check_main_file():
    """Быстрая проверка main.py"""
    main_path = Path("backend/main.py")
    if not main_path.exists():
        print("❌ Файл backend/main.py НЕ НАЙДЕН!")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'from flask import' in content:
        print("❌ main.py содержит Flask импорты - ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ")
        return False
    elif 'from fastapi import' in content:
        print("✅ main.py использует FastAPI")
        return True
    else:
        print("⚠️ main.py содержимое неопределенно")
        return False

def check_last_logs():
    """Проверка последних логов"""
    try:
        result = subprocess.run(['journalctl', '-u', 'chatumba', '-n', '3', '--no-pager'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("\n📋 Последние 3 строки логов:")
            print(result.stdout)
        else:
            print("❌ Не удалось получить логи")
    except Exception as e:
        print(f"❌ Ошибка получения логов: {e}")

def main():
    """Основная функция быстрой проверки"""
    print("⚡ БЫСТРАЯ ПРОВЕРКА СИСТЕМЫ IKAR")
    print("=" * 40)
    
    service_ok = check_service_status()
    main_ok = check_main_file()
    
    check_last_logs()
    
    print("\n" + "=" * 40)
    
    if service_ok and main_ok:
        print("✅ СИСТЕМА РАБОТАЕТ НОРМАЛЬНО")
    elif not main_ok:
        print("🔧 ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ:")
        print("   Запустите: python3 fix_system.py")
    elif not service_ok:
        print("🔄 ТРЕБУЕТСЯ ПЕРЕЗАПУСК:")
        print("   Запустите: sudo systemctl restart chatumba")
    else:
        print("❌ ТРЕБУЕТСЯ ДИАГНОСТИКА:")
        print("   Запустите: python3 diagnose_system.py")

if __name__ == "__main__":
    main() 