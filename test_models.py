#!/usr/bin/env python3
"""
Скрипт для проверки доступности моделей через OpenRouter API
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Модели для проверки (точно бесплатные)
MODELS_TO_TEST = [
    "openai/gpt-oss-20b:free",
    "deepseek/deepseek-chat-v3.1:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free",
    "google/gemma-2-2b:free"
]

# API ключи из .env
API_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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"
]

async def test_model(session, api_key, model):
    """Тестирует одну модель с одним API ключом"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ikar-assistant",
        "X-Title": "IKAR Assistant"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Привет! Как дела?"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        async with session.post(url, headers=headers, json=payload, timeout=10) as response:
            status_code = response.status
            response_text = await response.text()
            
            if status_code == 200:
                return {
                    "status": "✅ OK",
                    "model": model,
                    "api_key": api_key[:20] + "...",
                    "response": "Успешно"
                }
            else:
                return {
                    "status": f"❌ {status_code}",
                    "model": model,
                    "api_key": api_key[:20] + "...",
                    "response": response_text[:100] + "..." if len(response_text) > 100 else response_text
                }
                
    except asyncio.TimeoutError:
        return {
            "status": "⏰ TIMEOUT",
            "model": model,
            "api_key": api_key[:20] + "...",
            "response": "Превышено время ожидания"
        }
    except Exception as e:
        return {
            "status": f"💥 ERROR",
            "model": model,
            "api_key": api_key[:20] + "...",
            "response": str(e)[:100]
        }

async def main():
    print(f"🔍 Проверка моделей OpenRouter - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        # Тестируем каждую модель с каждым API ключом
        for model in MODELS_TO_TEST:
            print(f"\n📋 Тестируем модель: {model}")
            
            for i, api_key in enumerate(API_KEYS, 1):
                print(f"  🔑 API ключ #{i}...", end=" ")
                
                result = await test_model(session, api_key, model)
                results.append(result)
                
                print(result["status"])
                
                # Небольшая пауза между запросами
                await asyncio.sleep(0.5)
    
    # Выводим итоговую таблицу
    print("\n" + "=" * 80)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print("=" * 80)
    
    # Группируем результаты по моделям
    model_results = {}
    for result in results:
        model = result["model"]
        if model not in model_results:
            model_results[model] = []
        model_results[model].append(result)
    
    for model, model_tests in model_results.items():
        print(f"\n🤖 {model}")
        print("-" * 60)
        
        working_keys = []
        for test in model_tests:
            status = test["status"]
            # Находим номер ключа по началу
            key_num = "?"
            for i, key in enumerate(API_KEYS):
                if test["api_key"].startswith(key[:20]):
                    key_num = i + 1
                    break
            
            print(f"  Ключ #{key_num}: {status}")
            
            if "✅" in status:
                working_keys.append(key_num)
        
        if working_keys:
            print(f"  ✅ Рабочие ключи: {', '.join(map(str, working_keys))}")
        else:
            print(f"  ❌ Нет рабочих ключей для этой модели")
    
    # Статистика
    total_tests = len(results)
    successful_tests = len([r for r in results if "✅" in r["status"]])
    
    print(f"\n📈 СТАТИСТИКА:")
    print(f"  Всего тестов: {total_tests}")
    print(f"  Успешных: {successful_tests}")
    print(f"  Процент успеха: {(successful_tests/total_tests)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
