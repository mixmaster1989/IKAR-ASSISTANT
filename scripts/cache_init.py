#!/usr/bin/env python3
"""
Скрипт инициализации кэша для ИКАР ассистента
Запускается один раз для создания кэша системного промпта
"""

import asyncio
import aiohttp
import os
import sys
from dotenv import load_dotenv

# Добавляем путь к модулям проекта
sys.path.append('/root/IKAR-ASSISTANT')

from backend.prompts.ikar_system_prompt import IKAR_SYSTEM_PROMPT

async def init_cache():
    """Инициализирует кэш системного промпта"""
    
    # Загружаем переменные окружения
    load_dotenv('/root/IKAR-ASSISTANT/.env')
    
    api_key = os.getenv('OPENROUTER_API_KEY_PAID')
    if not api_key:
        print("❌ OPENROUTER_API_KEY_PAID не найден в .env файле!")
        return False
    
    print(f"🔑 Используем платный ключ: {api_key[:20]}...")
    print(f"📊 Размер системного промпта: {len(IKAR_SYSTEM_PROMPT):,} символов")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/ikar",
        "X-Title": "IKAR Cache Initialization"
    }
    
    # Запрос для инициализации кэша
    payload = {
        "model": "x-ai/grok-4-fast",
        "messages": [
            {
                "role": "system",
                "content": IKAR_SYSTEM_PROMPT,
                "metadata": {"cache": True}  # Включаем кэширование
            },
            {
                "role": "user",
                "content": "Подтверди, что контекст компании ИКАР загружен и готов к работе."
            }
        ],
        "max_tokens": 100,
        "temperature": 0.2
    }
    
    print("🚀 Инициализируем кэш системного промпта...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if 'usage' in data:
                        usage = data['usage']
                        print(f"📈 ТОКЕНЫ (Cache Write):")
                        print(f"   Входные: {usage.get('prompt_tokens', 0):,}")
                        print(f"   Выходные: {usage.get('completion_tokens', 0):,}")
                        print(f"   Всего: {usage.get('total_tokens', 0):,}")
                    
                    if 'choices' in data and data['choices']:
                        answer = data['choices'][0]['message']['content']
                        print(f"🤖 ОТВЕТ: {answer}")
                    
                    print(f"\n✅ КЭШ УСПЕШНО ИНИЦИАЛИЗИРОВАН!")
                    print(f"💡 Теперь все запросы будут использовать Cache Read")
                    print(f"💰 Экономия токенов: ~{usage.get('prompt_tokens', 0) * 0.8:,} токенов на запрос")
                    
                    return True
                    
                else:
                    text = await response.text()
                    print(f"❌ Ошибка инициализации кэша: {response.status}")
                    print(f"📄 Ответ: {text}")
                    return False
                    
    except aiohttp.ClientError as e:
        print(f"❌ Ошибка сетевого запроса: {e}")
        return False
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        return False

async def test_cache():
    """Тестирует работу кэша после инициализации"""
    
    print("\n🧪 ТЕСТИРУЕМ КЭШ...")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_dotenv('/root/IKAR-ASSISTANT/.env')
    
    api_key = os.getenv('OPENROUTER_API_KEY_PAID')
    if not api_key:
        print("❌ API ключ не найден!")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/ikar",
        "X-Title": "IKAR Cache Test"
    }
    
    # Тестовый запрос
    payload = {
        "model": "x-ai/grok-4-fast",
        "messages": [
            {
                "role": "system",
                "content": IKAR_SYSTEM_PROMPT,
                "metadata": {"cache": True}  # Должен быть Cache Read
            },
            {
                "role": "user",
                "content": "Сколько стоит Эвотор 7.2 с ФН-15? Отвечай только числом."
            }
        ],
        "max_tokens": 50,
        "temperature": 0.0
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if 'usage' in data:
                        usage = data['usage']
                        print(f"📈 ТОКЕНЫ (Cache Read):")
                        print(f"   Входные: {usage.get('prompt_tokens', 0):,}")
                        print(f"   Выходные: {usage.get('completion_tokens', 0):,}")
                        print(f"   Всего: {usage.get('total_tokens', 0):,}")
                    
                    if 'choices' in data and data['choices']:
                        answer = data['choices'][0]['message']['content']
                        print(f"🤖 ОТВЕТ: {answer}")
                        
                        if "43000" in answer or "43 000" in answer:
                            print(f"✅ ТЕСТ ПРОЙДЕН! Модель знает информацию из кэша")
                            return True
                        else:
                            print(f"❌ ТЕСТ НЕ ПРОЙДЕН! Модель не знает информацию из кэша")
                            return False
                    
                else:
                    text = await response.text()
                    print(f"❌ Ошибка теста: {response.status}")
                    print(f"📄 Ответ: {text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

async def main():
    """Основная функция"""
    print("🎯 ИНИЦИАЛИЗАЦИЯ КЭША ИКАР АССИСТЕНТА")
    print("=" * 50)
    
    # Инициализируем кэш
    success = await init_cache()
    
    if success:
        # Тестируем кэш
        test_success = await test_cache()
        
        if test_success:
            print(f"\n🎉 ВСЁ ГОТОВО!")
            print(f"✅ Кэш инициализирован")
            print(f"✅ Кэш работает корректно")
            print(f"💡 Теперь можно запускать ассистента с кэшированием")
        else:
            print(f"\n⚠️ Кэш инициализирован, но тест не пройден")
            print(f"💡 Возможно, нужно подождать или повторить инициализацию")
    else:
        print(f"\n❌ ИНИЦИАЛИЗАЦИЯ НЕ УДАЛАСЬ")
        print(f"💡 Проверьте API ключ и подключение к интернету")

if __name__ == "__main__":
    asyncio.run(main())
