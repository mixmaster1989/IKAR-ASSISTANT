#!/usr/bin/env python3
"""
Тест аутентификации всех ключей OpenRouter
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

async def test_key_auth(key, key_index):
    """Тестирует аутентификацию одного ключа"""
    
    key_suffix = key[-10:] if len(key) > 10 else key
    print(f"🔑 Ключ #{key_index + 1} (...{key_suffix})")
    
    # Простой запрос для проверки аутентификации
    base_url = "https://openrouter.ai/api/v1"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ikar-project/ikar",
        "X-Title": "IKAR Test"
    }
    
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5,
        "temperature": 0.3
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    print(f"   ✅ АУТЕНТИФИЦИРОВАН - работает!")
                    return True, "working"
                elif response.status == 401:
                    print(f"   ❌ НЕ АУТЕНТИФИЦИРОВАН - User not found")
                    return False, "auth_failed"
                elif response.status == 429:
                    print(f"   ⚠️  АУТЕНТИФИЦИРОВАН - Rate limit")
                    return True, "rate_limited"
                elif response.status == 402:
                    print(f"   ⚠️  АУТЕНТИФИЦИРОВАН - No credits")
                    return True, "no_credits"
                else:
                    print(f"   ❓ Статус {response.status}: {response_text[:100]}")
                    return False, f"status_{response.status}"
                    
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        return False, "exception"

async def test_all_keys():
    """Тестирует аутентификацию всех ключей"""
    
    print("🔍 ТЕСТ АУТЕНТИФИКАЦИИ ВСЕХ КЛЮЧЕЙ")
    print("=" * 50)
    
    # Получаем ключи
    config = Config()
    api_keys = get_all_openrouter_keys()
    
    if not api_keys:
        print("❌ НЕТ КЛЮЧЕЙ!")
        return
    
    print(f"📊 Всего ключей: {len(api_keys)}")
    print()
    
    # Тестируем каждый ключ
    auth_results = []
    
    for i, key in enumerate(api_keys):
        is_auth, status = await test_key_auth(key, i)
        auth_results.append((i + 1, is_auth, status))
        
        # Небольшая пауза между запросами
        await asyncio.sleep(0.5)
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ АУТЕНТИФИКАЦИИ")
    print("=" * 50)
    
    authenticated = [r for r in auth_results if r[1]]
    not_authenticated = [r for r in auth_results if not r[1]]
    
    print(f"✅ Аутентифицированных ключей: {len(authenticated)}")
    print(f"❌ НЕ аутентифицированных ключей: {len(not_authenticated)}")
    
    if authenticated:
        print(f"\n🎉 РАБОЧИЕ КЛЮЧИ:")
        for key_num, is_auth, status in authenticated:
            print(f"   #{key_num} - {status}")
    
    if not_authenticated:
        print(f"\n💥 НЕИСПРАВНЫЕ КЛЮЧИ:")
        for key_num, is_auth, status in not_authenticated:
            print(f"   #{key_num} - {status}")
    
    return auth_results

if __name__ == "__main__":
    asyncio.run(test_all_keys())
