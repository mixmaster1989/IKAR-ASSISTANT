#!/usr/bin/env python3
"""
Тест модели x-ai/grok-4-fast:free с твоим ключом
"""

import asyncio
import aiohttp
import json

async def test_grok_model():
    """Тестирует модель x-ai/grok-4-fast:free"""
    
    # Твой ключ
    test_key = "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"
    key_suffix = test_key[-10:] if len(test_key) > 10 else test_key
    
    print(f"🔍 ТЕСТ МОДЕЛИ x-ai/grok-4-fast:free")
    print("=" * 50)
    print(f"🔑 Ключ: ...{key_suffix}")
    print()
    
    # Тестовый запрос
    base_url = "https://openrouter.ai/api/v1"
    headers = {
        "Authorization": f"Bearer {test_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ikar-project/ikar",
        "X-Title": "IKAR Test"
    }
    
    # Простой текстовый запрос
    payload = {
        "model": "x-ai/grok-4-fast:free",
        "messages": [
            {
                "role": "user",
                "content": "Привет! Ответь одним словом на русском языке."
            }
        ],
        "max_tokens": 10,
        "temperature": 0.3
    }
    
    print(f"🧪 Тестируем модель: {payload['model']}")
    print(f"📤 Запрос: {payload['messages'][0]['content']}")
    
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
                print(f"📥 Ответ: {response_text}")
                
                if response.status == 200:
                    try:
                        response_data = json.loads(response_text)
                        if 'choices' in response_data and response_data['choices']:
                            content = response_data['choices'][0]['message']['content']
                            print(f"✅ УСПЕХ! Ответ: {content}")
                            return True
                        else:
                            print("⚠️ Нет choices в ответе")
                    except json.JSONDecodeError as e:
                        print(f"❌ Ошибка парсинга JSON: {e}")
                else:
                    print(f"❌ ОШИБКА {response.status}")
                    try:
                        error_data = json.loads(response_text)
                        print(f"📥 Детали ошибки: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"📥 Сырой ответ: {response_text}")
                        
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        import traceback
        print(f"📥 Traceback: {traceback.format_exc()}")
    
    return False

if __name__ == "__main__":
    result = asyncio.run(test_grok_model())
    if result:
        print("\n🎉 МОДЕЛЬ x-ai/grok-4-fast:free РАБОТАЕТ!")
    else:
        print("\n💥 МОДЕЛЬ НЕ РАБОТАЕТ!")
