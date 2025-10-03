#!/usr/bin/env python3
"""
Исправление проблем с импортом модулей
"""

import subprocess
import sys
import importlib

def force_reinstall_package(package_name):
    """Принудительно переустанавливает пакет"""
    try:
        print(f"🔄 Принудительно переустанавливаю {package_name}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--force-reinstall", "--no-cache-dir", package_name
        ], capture_output=True, text=True, check=True)
        print(f"✅ {package_name} переустановлен")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка переустановки {package_name}: {e.stderr}")
        return False

def install_with_user_flag(package_name):
    """Устанавливает пакет с флагом --user"""
    try:
        print(f"📦 Устанавливаю {package_name} с --user...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--user", "--no-cache-dir", package_name
        ], capture_output=True, text=True, check=True)
        print(f"✅ {package_name} установлен с --user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package_name}: {e.stderr}")
        return False

def check_module(module_name):
    """Проверяет, работает ли импорт модуля"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def main():
    print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМ С ИМПОРТОМ")
    print("=" * 50)
    
    # Проблемные модули
    problematic_modules = [
        ("newspaper3k", "newspaper3k"),
        ("attrs", "attrs"),
        ("langdetect", "langdetect")
    ]
    
    print("🔍 Проверяю текущее состояние...")
    for module_name, package_name in problematic_modules:
        if check_module(module_name):
            print(f"✅ {module_name} - уже работает")
        else:
            print(f"❌ {module_name} - не работает")
    
    print("\n🔄 ИСПРАВЛЕНИЕ...")
    print("=" * 50)
    
    for module_name, package_name in problematic_modules:
        if not check_module(module_name):
            print(f"\n🔧 Исправляю {module_name}...")
            
            # Сначала пробуем принудительную переустановку
            if force_reinstall_package(package_name):
                if check_module(module_name):
                    print(f"✅ {module_name} исправлен!")
                    continue
            
            # Если не помогло, пробуем с --user
            if install_with_user_flag(package_name):
                if check_module(module_name):
                    print(f"✅ {module_name} исправлен с --user!")
                    continue
            
            print(f"❌ Не удалось исправить {module_name}")
    
    print("\n🔍 ФИНАЛЬНАЯ ПРОВЕРКА...")
    print("=" * 50)
    
    all_working = True
    for module_name, package_name in problematic_modules:
        if check_module(module_name):
            print(f"✅ {module_name} - работает")
        else:
            print(f"❌ {module_name} - все еще не работает")
            all_working = False
    
    if all_working:
        print("\n🎉 ВСЕ МОДУЛИ ИСПРАВЛЕНЫ!")
    else:
        print("\n⚠️  Некоторые модули все еще не работают")
        print("Попробуйте:")
        print("1. Перезапустить терминал")
        print("2. Проверить переменную PYTHONPATH")
        print("3. Установить модули вручную")

if __name__ == "__main__":
    main() 