#!/usr/bin/env python3
"""
Диагностический скрипт для проверки системы IKAR
Проверяет все компоненты и выводит подробную информацию
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def print_section(title):
    """Красивый вывод секции"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_python_version():
    """Проверка версии Python"""
    print_section("ПРОВЕРКА PYTHON")
    print(f"Python версия: {sys.version}")
    print(f"Python путь: {sys.executable}")
    print(f"Рабочая директория: {os.getcwd()}")

def check_main_file():
    """Проверка основного файла"""
    print_section("ПРОВЕРКА MAIN.PY")
    
    main_path = Path("backend/main.py")
    if not main_path.exists():
        print("❌ Файл backend/main.py НЕ НАЙДЕН!")
        return False
    
    print(f"✅ Файл найден: {main_path.absolute()}")
    
    # Читаем первые 20 строк
    with open(main_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:20]
    
    print("\n📄 Первые 20 строк файла:")
    for i, line in enumerate(lines, 1):
        print(f"{i:2d}: {line.rstrip()}")
    
    # Проверяем импорты
    flask_imports = [line for line in lines if 'from flask import' in line or 'import flask' in line]
    fastapi_imports = [line for line in lines if 'from fastapi import' in line or 'import fastapi' in line]
    
    print(f"\n🔍 Flask импорты: {len(flask_imports)}")
    for imp in flask_imports:
        print(f"   ❌ {imp.strip()}")
    
    print(f"🔍 FastAPI импорты: {len(fastapi_imports)}")
    for imp in fastapi_imports:
        print(f"   ✅ {imp.strip()}")
    
    return len(flask_imports) == 0 and len(fastapi_imports) > 0

def check_requirements():
    """Проверка зависимостей"""
    print_section("ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    
    # Проверяем requirements.txt
    req_path = Path("requirements.txt")
    if req_path.exists():
        print("✅ requirements.txt найден")
        with open(req_path, 'r') as f:
            reqs = f.read()
        
        if 'flask' in reqs.lower():
            print("❌ В requirements.txt найден Flask!")
        if 'fastapi' in reqs.lower():
            print("✅ В requirements.txt найден FastAPI")
    else:
        print("❌ requirements.txt НЕ НАЙДЕН!")
    
    # Проверяем установленные пакеты
    critical_packages = ['fastapi', 'uvicorn', 'pydantic', 'starlette']
    
    for package in critical_packages:
        try:
            spec = importlib.util.find_spec(package)
            if spec is not None:
                print(f"✅ {package} установлен")
            else:
                print(f"❌ {package} НЕ УСТАНОВЛЕН!")
        except ImportError:
            print(f"❌ {package} НЕ УСТАНОВЛЕН!")

def check_systemd_service():
    """Проверка systemd сервиса"""
    print_section("ПРОВЕРКА SYSTEMD СЕРВИСА")
    
    try:
        # Проверяем статус сервиса
        result = subprocess.run(['systemctl', 'is-active', 'chatumba'], 
                              capture_output=True, text=True)
        print(f"Статус сервиса: {result.stdout.strip()}")
        
        # Получаем конфигурацию сервиса
        result = subprocess.run(['systemctl', 'cat', 'chatumba'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("\n📋 Конфигурация сервиса:")
            print(result.stdout)
        else:
            print("❌ Не удалось получить конфигурацию сервиса")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке systemd: {e}")

def check_logs():
    """Проверка логов"""
    print_section("ПРОВЕРКА ЛОГОВ")
    
    try:
        # Последние 10 строк логов
        result = subprocess.run(['journalctl', '-u', 'chatumba', '-n', '10', '--no-pager'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("📋 Последние 10 строк логов:")
            print(result.stdout)
        else:
            print("❌ Не удалось получить логи")
            
    except Exception as e:
        print(f"❌ Ошибка при получении логов: {e}")

def check_file_permissions():
    """Проверка прав доступа"""
    print_section("ПРОВЕРКА ПРАВ ДОСТУПА")
    
    files_to_check = [
        "backend/main.py",
        "backend/config.py",
        "backend/api/collective_api.py",
        "backend/api/memory_api.py",
        "requirements.txt"
    ]
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            stat = path.stat()
            print(f"✅ {file_path}: {oct(stat.st_mode)[-3:]}")
        else:
            print(f"❌ {file_path}: НЕ НАЙДЕН")

def check_imports():
    """Проверка импортов в Python"""
    print_section("ПРОВЕРКА ИМПОРТОВ")
    
    # Пытаемся импортировать основные модули
    test_imports = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'starlette',
        'aiohttp',
        'aiosqlite'
    ]
    
    for module in test_imports:
        try:
            __import__(module)
            print(f"✅ {module} импортируется успешно")
        except ImportError as e:
            print(f"❌ {module} НЕ ИМПОРТИРУЕТСЯ: {e}")

def main():
    """Основная функция диагностики"""
    print("🚀 ДИАГНОСТИКА СИСТЕМЫ IKAR")
    print("=" * 60)
    
    # Проверяем все компоненты
    check_python_version()
    check_main_file()
    check_requirements()
    check_file_permissions()
    check_imports()
    check_systemd_service()
    check_logs()
    
    print_section("РЕКОМЕНДАЦИИ")
    
    # Проверяем, нужно ли обновить main.py
    main_path = Path("backend/main.py")
    if main_path.exists():
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'from flask import' in content:
            print("🔧 ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ:")
            print("   1. Файл backend/main.py содержит импорты Flask")
            print("   2. Необходимо обновить файл до версии с FastAPI")
            print("   3. Запустите: git pull для получения последних изменений")
        else:
            print("✅ Файл backend/main.py выглядит корректно")
    
    print("\n🔄 КОМАНДЫ ДЛЯ ИСПРАВЛЕНИЯ:")
    print("1. git pull                           # Получить последние изменения")
    print("2. pip install -r requirements.txt   # Установить зависимости")
    print("3. sudo systemctl restart chatumba   # Перезапустить сервис")
    print("4. sudo journalctl -u chatumba -f    # Посмотреть логи")

if __name__ == "__main__":
    main() 