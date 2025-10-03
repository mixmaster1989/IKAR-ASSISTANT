#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов системы FAISS.
"""

import asyncio
import sys
import os
from datetime import datetime

def print_banner():
    """Выводит баннер тестирования"""
    print("=" * 70)
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ FAISS И ПЕРЕЗАПИСИ ПАМЯТИ")
    print("=" * 70)
    print(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔧 Тестирование на реальных данных с OpenRouter")
    print("=" * 70)

async def run_basic_test():
    """Запуск базового теста"""
    print("\n🚀 ЗАПУСК БАЗОВОГО ТЕСТА...")
    print("-" * 40)
    
    try:
        from test_faiss_full_system import FAISSFullSystemTest
        test = FAISSFullSystemTest()
        result = await test.run_all_tests()
        return result
    except Exception as e:
        print(f"❌ Ошибка запуска базового теста: {e}")
        return False

async def run_stress_test():
    """Запуск стресс-теста"""
    print("\n🚀 ЗАПУСК СТРЕСС-ТЕСТА...")
    print("-" * 40)
    
    try:
        from test_faiss_stress import FAISSStressTest
        test = FAISSStressTest()
        result = await test.run_stress_tests()
        return result
    except Exception as e:
        print(f"❌ Ошибка запуска стресс-теста: {e}")
        return False

async def main():
    """Главная функция"""
    print_banner()
    
    # Проверяем наличие файлов тестов
    test_files = [
        "test_faiss_full_system.py",
        "test_faiss_stress.py"
    ]
    
    missing_files = []
    for file in test_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы тестов: {', '.join(missing_files)}")
        print("Убедитесь, что все файлы тестов находятся в текущей директории.")
        sys.exit(1)
    
    # Запускаем тесты
    basic_success = await run_basic_test()
    stress_success = await run_stress_test()
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 70)
    
    if basic_success:
        print("✅ Базовый тест: ПРОЙДЕН")
    else:
        print("❌ Базовый тест: ПРОВАЛЕН")
    
    if stress_success:
        print("✅ Стресс-тест: ПРОЙДЕН")
    else:
        print("❌ Стресс-тест: ПРОВАЛЕН")
    
    if basic_success and stress_success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("Система FAISS и перезаписи памяти работает корректно.")
        sys.exit(0)
    else:
        print("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        print("Проверьте логи для деталей.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 