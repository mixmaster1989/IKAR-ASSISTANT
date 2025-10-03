#!/usr/bin/env python3
"""
Тест OpenRouter API на архитектуре проекта IKAR
Проверяет все доступные ключи и их работоспособность
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Добавляем путь к backend для импортов
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.config import Config, get_all_openrouter_keys
from backend.llm.openrouter import OpenRouterClient
from backend.utils.logger import get_logger

logger = get_logger('openrouter_test')

async def test_openrouter_keys():
    """Тестирует все доступные OpenRouter API ключи"""
    
    print("🔍 ТЕСТ OPENROUTER API КЛЮЧЕЙ")
    print("=" * 50)
    
    # Получаем все ключи из конфига
    config = Config()
    api_keys = get_all_openrouter_keys()
    
    print(f"📊 Найдено ключей: {len(api_keys)}")
    
    if not api_keys:
        print("❌ НЕТ КЛЮЧЕЙ! Проверьте переменные окружения:")
        print("   - OPENROUTER_API_KEY")
        print("   - OPENROUTER_API_KEY_2, OPENROUTER_API_KEY_3, etc.")
        return
    
    # Создаем клиент
    client = OpenRouterClient(config)
    
    # Тестовый промпт
    test_prompt = "Привет! Ответь одним предложением на русском языке."
    
    print(f"\n🧪 Тестовый промпт: {test_prompt}")
    print("\n" + "=" * 50)
    
    # Тестируем каждый ключ
    working_keys = []
    failed_keys = []
    
    for i, key in enumerate(api_keys, 1):
        key_suffix = key[-10:] if len(key) > 10 else key
        print(f"\n🔑 Тестируем ключ #{i} (...{key_suffix})")
        
        try:
            # Устанавливаем текущий ключ
            client.current_key_index = i - 1
            
            start_time = time.time()
            
            # Простой запрос с БЕСПЛАТНОЙ моделью
            response = await client.generate_response(
                prompt=test_prompt,
                use_memory=False,  # Отключаем память для чистого теста
                model="deepseek/deepseek-r1-0528:free",  # Используем БЕСПЛАТНУЮ модель
                max_tokens=100,
                temperature=0.3
            )
            
            response_time = time.time() - start_time
            
            if response and len(response.strip()) > 0:
                print(f"✅ УСПЕХ! Время: {response_time:.2f}с")
                print(f"📝 Ответ: {response[:100]}...")
                working_keys.append((i, key_suffix, response_time))
            else:
                print(f"❌ ПУСТОЙ ОТВЕТ")
                failed_keys.append((i, key_suffix, "empty_response"))
                
        except Exception as e:
            print(f"❌ ОШИБКА: {str(e)[:100]}...")
            failed_keys.append((i, key_suffix, str(e)[:50]))
        
        # Небольшая пауза между тестами
        await asyncio.sleep(1)
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    print(f"✅ Рабочих ключей: {len(working_keys)}")
    print(f"❌ Неисправных ключей: {len(failed_keys)}")
    
    if working_keys:
        print(f"\n🎉 РАБОЧИЕ КЛЮЧИ:")
        for i, suffix, time_taken in working_keys:
            print(f"   #{i} (...{suffix}) - {time_taken:.2f}с")
    
    if failed_keys:
        print(f"\n💥 НЕИСПРАВНЫЕ КЛЮЧИ:")
        for i, suffix, error in failed_keys:
            print(f"   #{i} (...{suffix}) - {error}")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    if len(working_keys) == 0:
        print("   🚨 ВСЕ КЛЮЧИ НЕ РАБОТАЮТ!")
        print("   - Проверьте правильность ключей")
        print("   - Проверьте баланс на OpenRouter")
        print("   - Проверьте интернет соединение")
    elif len(working_keys) < len(api_keys) // 2:
        print("   ⚠️  МНОГО НЕИСПРАВНЫХ КЛЮЧЕЙ")
        print("   - Обновите неисправные ключи")
        print("   - Проверьте баланс на OpenRouter")
    else:
        print("   ✅ СИСТЕМА РАБОТАЕТ НОРМАЛЬНО")
        print("   - Достаточно рабочих ключей для ротации")
    
    return {
        'total_keys': len(api_keys),
        'working_keys': len(working_keys),
        'failed_keys': len(failed_keys),
        'working_details': working_keys,
        'failed_details': failed_keys
    }

async def test_memory_integration():
    """Тестирует интеграцию с памятью"""
    
    print("\n" + "=" * 50)
    print("🧠 ТЕСТ ИНТЕГРАЦИИ С ПАМЯТЬЮ")
    print("=" * 50)
    
    try:
        config = Config()
        client = OpenRouterClient(config)
        
        # Тест с памятью
        memory_prompt = "Что ты помнишь о важных событиях?"
        
        print(f"🧪 Тестовый промпт: {memory_prompt}")
        
        start_time = time.time()
        response = await client.generate_response(
            prompt=memory_prompt,
            use_memory=True,
            max_tokens=200,
            temperature=0.5
        )
        response_time = time.time() - start_time
        
        if response:
            print(f"✅ ПАМЯТЬ РАБОТАЕТ! Время: {response_time:.2f}с")
            print(f"📝 Ответ: {response[:200]}...")
            
            # Статистика памяти
            stats = client.get_memory_stats()
            print(f"📊 Статистика памяти: {stats}")
            
        else:
            print("❌ ПАМЯТЬ НЕ РАБОТАЕТ - пустой ответ")
            
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА ПАМЯТИ: {e}")

async def test_fallback_models():
    """Тестирует fallback модели"""
    
    print("\n" + "=" * 50)
    print("🔄 ТЕСТ FALLBACK МОДЕЛЕЙ")
    print("=" * 50)
    
    try:
        config = Config()
        client = OpenRouterClient(config)
        
        # Тест основной модели
        print("🧪 Тестируем основную модель...")
        response1 = await client.generate_response(
            prompt="Скажи 'Привет' на русском",
            model=client.default_model,
            use_memory=False,
            max_tokens=50
        )
        
        if response1:
            print(f"✅ Основная модель работает: {response1[:50]}...")
        else:
            print("❌ Основная модель не работает")
        
        # Тест fallback модели
        print("🧪 Тестируем fallback модель...")
        response2 = await client.generate_response(
            prompt="Скажи 'Привет' на русском",
            model=client.fallback_model,
            use_memory=False,
            max_tokens=50
        )
        
        if response2:
            print(f"✅ Fallback модель работает: {response2[:50]}...")
        else:
            print("❌ Fallback модель не работает")
            
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА FALLBACK: {e}")

async def main():
    """Главная функция тестирования"""
    
    print("🚀 ЗАПУСК ТЕСТОВ OPENROUTER API")
    print("=" * 60)
    
    # Проверяем переменные окружения
    print("🔍 Проверяем переменные окружения...")
    env_vars = [k for k in os.environ.keys() if k.startswith('OPENROUTER_API_KEY')]
    print(f"📋 Найдено переменных: {env_vars}")
    
    # Основной тест ключей
    result = await test_openrouter_keys()
    
    # Тест памяти (только если есть рабочие ключи)
    if result and result['working_keys'] > 0:
        await test_memory_integration()
        await test_fallback_models()
    else:
        print("\n⚠️  Пропускаем тесты памяти и fallback - нет рабочих ключей")
    
    print("\n" + "=" * 60)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
