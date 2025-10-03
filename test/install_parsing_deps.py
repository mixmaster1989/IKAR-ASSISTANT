#!/usr/bin/env python3
"""
Быстрая установка всех зависимостей парсинга
"""

import subprocess
import sys

def install_package(package_name):
    """Устанавливает пакет через pip"""
    try:
        print(f"📦 Устанавливаю {package_name}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {package_name} установлен")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package_name}: {e.stderr}")
        return False

def main():
    print("🚀 БЫСТРАЯ УСТАНОВКА ЗАВИСИМОСТЕЙ ПАРСИНГА")
    print("=" * 50)
    
    # Критические зависимости для парсинга
    critical_deps = [
        "trafilatura",
        "newspaper3k", 
        "readability-lxml",
        "justext",
        "beautifulsoup4",
        "lxml",
        "requests",
        "aiohttp",
        "feedparser",
        "htmldate",
        "langdetect",
        "nltk",
        "textstat",
        "python-dateutil"
    ]
    
    success_count = 0
    failed_count = 0
    
    for package in critical_deps:
        if install_package(package):
            success_count += 1
        else:
            failed_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТ: {success_count} успешно, {failed_count} неудачно")
    
    if failed_count == 0:
        print("🎉 ВСЕ ЗАВИСИМОСТИ УСТАНОВЛЕНЫ УСПЕШНО!")
    else:
        print(f"⚠️  {failed_count} пакетов не удалось установить")
        print("Попробуйте установить их вручную или проверьте права доступа")

if __name__ == "__main__":
    main() 