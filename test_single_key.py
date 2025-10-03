#!/usr/bin/env python3
"""
Тест одного ключа OpenRouter с детальным логированием ошибок
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

async def test_single_key():
    """Тестирует один ключ с детальным логированием"""
    
    print("🔍 ТЕСТ ОДНОГО КЛЮЧА OPENROUTER")
    print("=" * 50)
    
    # Получаем ключи
    config = Config()
    api_keys = get_all_openrouter_keys()
    
    if not api_keys:
        print("❌ НЕТ КЛЮЧЕЙ!")
        return
    
    # Берем первый ключ
    test_key = api_keys[0]
    key_suffix = test_key[-10:] if len(test_key) > 10 else test_key
    
    print(f"🔑 Тестируем ключ: ...{key_suffix}")
    print(f"📊 Всего ключей: {len(api_keys)}")
    
    # Тестовый запрос
    base_url = "https://openrouter.ai/api/v1"
    headers = {
        "Authorization": f"Bearer {test_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ikar-project/ikar",
        "X-Title": "IKAR Test"
    }
    
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {
                "role": "user",
                "content": "Привет! Ответь одним словом на русском языке."
            }
        ],
        "max_tokens": 10,
        "temperature": 0.3
    }
    
    print(f"📤 Отправляем запрос к модели: {payload['model']}")
    print(f"📤 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                print(f"📥 Статус ответа: {response.status}")
                print(f"📥 Заголовки ответа: {dict(response.headers)}")
                
                # Читаем ответ
                response_text = await response.text()
                print(f"📥 Текст ответа: {response_text}")
                
                if response.status == 200:
                    try:
                        response_data = json.loads(response_text)
                        print(f"✅ УСПЕХ! Ответ: {response_data}")
                        
                        if 'choices' in response_data and response_data['choices']:
                            content = response_data['choices'][0]['message']['content']
                            print(f"🎉 Сгенерированный текст: {content}")
                        else:
                            print("⚠️ Нет choices в ответе")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Ошибка парсинга JSON: {e}")
                        print(f"📥 Сырой ответ: {response_text}")
                        
                else:
                    print(f"❌ ОШИБКА HTTP {response.status}")
                    print(f"📥 Детали ошибки: {response_text}")
                    
                    # Пытаемся распарсить ошибку
                    try:
                        error_data = json.loads(response_text)
                        print(f"📥 Структурированная ошибка: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    except:
                        print("📥 Ошибка не в JSON формате")
                        
    except asyncio.TimeoutError:
        print("❌ ТАЙМАУТ - запрос не выполнился за 30 секунд")
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {type(e).__name__}: {e}")
        import traceback
        print(f"📥 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_single_key())
