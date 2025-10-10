#!/usr/bin/env python3
"""
Тест платной модели OpenRouter
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv('/root/IKAR-ASSISTANT/.env')

async def test_paid_model():
    """Тестируем платную модель"""
    
    api_key = os.getenv('OPENROUTER_API_KEY_PAID')
    if not api_key:
        print("❌ Платный ключ не найден!")
        return
    
    print(f"🔑 Используем ключ: {api_key[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/ikar",
        "X-Title": "IKAR Test"
    }
    
    # Тестируем с простым промптом
    payload = {
        "model": "x-ai/grok-4-fast",
        "messages": [
            {
                "role": "user",
                "content": "Привет! Ответь коротко: как дела?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.3
    }
    
    print("🚀 Отправляем запрос к Grok 4 Fast...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                print(f"📊 Статус ответа: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Показываем usage
                    if 'usage' in data:
                        usage = data['usage']
                        print(f"📈 ТОКЕНЫ:")
                        print(f"   Входные: {usage.get('prompt_tokens', 0):,}")
                        print(f"   Выходные: {usage.get('completion_tokens', 0):,}")
                        print(f"   Всего: {usage.get('total_tokens', 0):,}")
                    
                    # Показываем ответ
                    if 'choices' in data and data['choices']:
                        answer = data['choices'][0]['message']['content']
                        print(f"🤖 ОТВЕТ: {answer}")
                        print("✅ Платная модель работает!")
                    else:
                        print("❌ Нет ответа в данных")
                        print(f"📄 Полный ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    text = await response.text()
                    print(f"❌ Ошибка {response.status}: {text}")
                    
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    asyncio.run(test_paid_model())
