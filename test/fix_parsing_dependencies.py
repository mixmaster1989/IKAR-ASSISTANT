#!/usr/bin/env python3
"""
Скрипт для проверки и установки зависимостей парсинга
"""

import subprocess
import sys
import importlib

def check_module(module_name):
    """Проверяет, установлен ли модуль"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """Устанавливает пакет через pip"""
    try:
        print(f"📦 Устанавливаю {package_name}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {package_name} установлен успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package_name}: {e.stderr}")
        return False

def main():
    print("🔍 ПРОВЕРКА ЗАВИСИМОСТЕЙ ПАРСИНГА")
    print("=" * 50)
    
    # Список необходимых модулей и их пакетов
    dependencies = [
        ("trafilatura", "trafilatura"),
        ("newspaper3k", "newspaper3k"),
        ("readability", "readability-lxml"),
        ("justext", "justext"),
        ("beautifulsoup4", "beautifulsoup4"),
        ("lxml", "lxml"),
        ("requests", "requests"),
        ("aiohttp", "aiohttp"),
        ("feedparser", "feedparser"),
        ("htmldate", "htmldate"),
        ("langdetect", "langdetect"),
        ("nltk", "nltk"),
        ("textstat", "textstat"),
        ("python-dateutil", "python-dateutil"),
        ("urllib3", "urllib3"),
        ("certifi", "certifi"),
        ("charset-normalizer", "charset-normalizer"),
        ("idna", "idna"),
        ("multidict", "multidict"),
        ("yarl", "yarl"),
        ("async-timeout", "async-timeout"),
        ("attrs", "attrs"),
        ("typing-extensions", "typing-extensions")
    ]
    
    missing_modules = []
    installed_count = 0
    
    print("📋 Проверяю установленные модули...")
    
    for module_name, package_name in dependencies:
        if check_module(module_name):
            print(f"✅ {module_name} - установлен")
        else:
            print(f"❌ {module_name} - НЕ УСТАНОВЛЕН")
            missing_modules.append((module_name, package_name))
    
    print(f"\n📊 РЕЗУЛЬТАТ: {len(dependencies) - len(missing_modules)}/{len(dependencies)} модулей установлено")
    
    if missing_modules:
        print(f"\n🚨 НАЙДЕНО {len(missing_modules)} ОТСУТСТВУЮЩИХ МОДУЛЕЙ")
        print("=" * 50)
        
        response = input("Установить недостающие модули? (y/n): ").lower().strip()
        
        if response in ['y', 'yes', 'да', 'д']:
            print("\n🔧 УСТАНОВКА МОДУЛЕЙ...")
            print("=" * 50)
            
            for module_name, package_name in missing_modules:
                if install_package(package_name):
                    installed_count += 1
                else:
                    print(f"⚠️  Пропускаю {module_name} из-за ошибки установки")
            
            print(f"\n📈 УСТАНОВЛЕНО: {installed_count}/{len(missing_modules)} модулей")
            
            # Проверяем еще раз после установки
            print("\n🔍 ПОВТОРНАЯ ПРОВЕРКА...")
            still_missing = []
            for module_name, package_name in missing_modules:
                if check_module(module_name):
                    print(f"✅ {module_name} - теперь установлен")
                else:
                    print(f"❌ {module_name} - все еще не установлен")
                    still_missing.append(module_name)
            
            if still_missing:
                print(f"\n⚠️  ВНИМАНИЕ: {len(still_missing)} модулей все еще не установлены:")
                for module in still_missing:
                    print(f"   - {module}")
                print("\nПопробуйте установить их вручную или проверьте права доступа")
            else:
                print("\n🎉 ВСЕ МОДУЛИ УСПЕШНО УСТАНОВЛЕНЫ!")
        else:
            print("❌ Установка отменена пользователем")
    else:
        print("\n🎉 ВСЕ ЗАВИСИМОСТИ УЖЕ УСТАНОВЛЕНЫ!")
    
    print("\n" + "=" * 50)
    print("🔧 ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ")
    
    # Проверяем версии критических модулей
    critical_modules = ["trafilatura", "newspaper3k", "beautifulsoup4", "requests"]
    for module in critical_modules:
        if check_module(module):
            try:
                module_obj = importlib.import_module(module)
                if hasattr(module_obj, '__version__'):
                    print(f"📦 {module} версия: {module_obj.__version__}")
                else:
                    print(f"📦 {module} - установлен (версия неизвестна)")
            except Exception as e:
                print(f"⚠️  {module} - ошибка получения версии: {e}")
    
    print("\n✅ ПРОВЕРКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    main() 