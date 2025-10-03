#!/usr/bin/env python3
"""
Диагностика проблем с импортом модулей
"""

import sys
import subprocess
import importlib

def check_pip_install(package_name):
    """Проверяет, установлен ли пакет через pip"""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "show", package_name], 
                              capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError:
        return False, ""

def check_module_import(module_name):
    """Проверяет импорт модуля"""
    try:
        module = importlib.import_module(module_name)
        return True, f"Версия: {getattr(module, '__version__', 'неизвестна')}"
    except ImportError as e:
        return False, str(e)

def main():
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМ С ИМПОРТОМ")
    print("=" * 60)
    
    print(f"🐍 Python версия: {sys.version}")
    print(f"📁 Python путь: {sys.executable}")
    print(f"📂 Пути поиска модулей:")
    for i, path in enumerate(sys.path):
        print(f"   {i+1}. {path}")
    
    print("\n" + "=" * 60)
    
    # Проблемные модули
    problematic_modules = [
        ("newspaper3k", "newspaper3k"),
        ("beautifulsoup4", "bs4"),
        ("langdetect", "langdetect"),
        ("python-dateutil", "dateutil"),
        ("charset-normalizer", "charset_normalizer"),
        ("async-timeout", "async_timeout"),
        ("attrs", "attrs"),
        ("typing-extensions", "typing_extensions")
    ]
    
    for package_name, module_name in problematic_modules:
        print(f"\n🔍 Проверяю {package_name} ({module_name}):")
        
        # Проверяем установку через pip
        pip_installed, pip_info = check_pip_install(package_name)
        if pip_installed:
            print(f"   ✅ pip: установлен")
            # Показываем информацию о пакете
            lines = pip_info.split('\n')
            for line in lines:
                if line.startswith('Location:'):
                    print(f"   📍 {line}")
                    break
        else:
            print(f"   ❌ pip: НЕ установлен")
        
        # Проверяем импорт
        import_success, import_info = check_module_import(module_name)
        if import_success:
            print(f"   ✅ import: работает - {import_info}")
        else:
            print(f"   ❌ import: НЕ работает - {import_info}")
    
    print("\n" + "=" * 60)
    print("🔧 РЕКОМЕНДАЦИИ:")
    
    # Проверяем виртуальное окружение
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Виртуальное окружение: активно")
    else:
        print("⚠️  Виртуальное окружение: НЕ активно")
        print("   Рекомендуется использовать виртуальное окружение")
    
    # Проверяем права доступа
    import os
    try:
        test_file = os.path.join(sys.prefix, 'test_write_permission')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ Права записи: есть")
    except Exception as e:
        print(f"❌ Права записи: НЕТ - {e}")
    
    print("\n💡 ВОЗМОЖНЫЕ РЕШЕНИЯ:")
    print("1. Перезапустите Python после установки пакетов")
    print("2. Проверьте, что используете правильное виртуальное окружение")
    print("3. Попробуйте: pip install --force-reinstall <package>")
    print("4. Проверьте права доступа к папкам Python")

if __name__ == "__main__":
    main() 