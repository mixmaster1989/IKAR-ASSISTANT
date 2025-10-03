#!/usr/bin/env python3
"""
Тест конкретно ключа 5 с правильными заголовками
"""

import asyncio
import aiohttp
import json
import os
import sys
from pathlib import Path

# Добавляем путь к backend для импортов
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.config import Config, get_all_openrouter_keys

async def test_key5():
    """Тестирует ключ 5 с правильными заголовками"""
    
    print("🔍 ТЕСТ КЛЮЧА 5 OPENROUTER")
    print("=" * 50)
    
    # Получаем ключи
    config = Config()
    api_keys = get_all_openrouter_keys()
    
    if not api_keys or len(api_keys) < 5:
        print("❌ НЕТ КЛЮЧА 5!")
        return
    
    # Берем ключ 5 (индекс 4)
    test_key = api_keys[4]  # Ключ 5
    key_suffix = test_key[-10:] if len(test_key) > 10 else test_key
    
    print(f"🔑 Тестируем ключ 5: ...{key_suffix}")
    
    # Тестовый запрос с ПРАВИЛЬНЫМИ заголовками
    base_url = "https://openrouter.ai/api/v1"
    headers = {
        "Authorization": f"Bearer {test_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ikar-project/ikar",
        "X-Title": "IKAR Test"
    }
    
    # Пробуем разные модели
    models_to_test = [
        "deepseek/deepseek-r1-0528:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free"
    ]
    
    for model in models_to_test:
        print(f"\n🧪 Тестируем модель: {model}")
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": "Hi"
                }
            ],
            "max_tokens": 10,
            "temperature": 0.3
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    print(f"📥 Статус: {response.status}")
                    
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            response_data = json.loads(response_text)
                            if 'choices' in response_data and response_data['choices']:
                                content = response_data['choices'][0]['message']['content']
                                print(f"✅ УСПЕХ! Ответ: {content}")
                                return True
                        except json.JSONDecodeError:
                            print(f"❌ Ошибка парсинга JSON")
                    else:
                        print(f"❌ ОШИБКА {response.status}: {response_text}")
                        
        except Exception as e:
            print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
    
    return False

if __name__ == "__main__":
    result = asyncio.run(test_key5())
    if result:
        print("\n🎉 КЛЮЧ 5 РАБОТАЕТ!")
    else:
        print("\n💥 КЛЮЧ 5 НЕ РАБОТАЕТ!")
