#!/usr/bin/env python3
"""
Тест модели openai/gpt-oss-120b:free с твоим ключом
"""

import asyncio
import aiohttp
import json

async def test_gpt_oss():
    """Тестирует модель openai/gpt-oss-120b:free"""
    
    # Твой ключ
    test_key = "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"
    key_suffix = test_key[-10:] if len(test_key) > 10 else test_key
    
    print(f"🔍 ТЕСТ МОДЕЛИ openai/gpt-oss-120b:free")
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
    
    # Запрос как в примере
    payload = {
        "model": "openai/gpt-oss-120b:free",
        "messages": [
            {
                "role": "user",
                "content": "What is the meaning of life?"
            }
        ]
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
    result = asyncio.run(test_gpt_oss())
    if result:
        print("\n🎉 МОДЕЛЬ openai/gpt-oss-120b:free РАБОТАЕТ!")
    else:
        print("\n💥 МОДЕЛЬ НЕ РАБОТАЕТ!")
