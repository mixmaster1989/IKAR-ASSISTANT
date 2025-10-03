#!/usr/bin/env python3
"""
Тест конкретного ключа OpenRouter
"""

import asyncio
import aiohttp
import json

async def test_specific_key():
    """Тестирует конкретный ключ"""
    
    # Ключ который ты дал
    test_key = "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"
    key_suffix = test_key[-10:] if len(test_key) > 10 else test_key
    
    print(f"🔍 ТЕСТ КОНКРЕТНОГО КЛЮЧА")
    print("=" * 50)
    print(f"🔑 Ключ: ...{key_suffix}")
    print(f"📊 Длина: {len(test_key)}")
    print(f"📊 Начинается с: {test_key[:10]}")
    print()
    
    # Тестовый запрос
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
        "microsoft/phi-3-mini-128k-instruct:free",
        "google/gemini-flash-1.5:free"
    ]
    
    for model in models_to_test:
        print(f"🧪 Тестируем модель: {model}")
        
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
                    timeout=aiohttp.ClientTimeout(total=15)
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
        
        print()
    
    return False

if __name__ == "__main__":
    result = asyncio.run(test_specific_key())
    if result:
        print("🎉 КЛЮЧ РАБОТАЕТ!")
    else:
        print("💥 КЛЮЧ НЕ РАБОТАЕТ!")
