#!/usr/bin/env python3
"""
🔍 Поиск РАБОЧИХ моделей text-to-image на Hugging Face
- Ищет модели через API поиска
- Проверяет их доступность через Inference API
- Тестирует реальную генерацию
- Сохраняет только рабочие модели
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import aiohttp

# Загрузка .env
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

HF_TOKEN = os.environ.get('HF_API_KEY') or os.environ.get('HF_API_TOKEN') or os.environ.get('HUGGINGFACEHUB_API_TOKEN') or ''

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
REPORTS.mkdir(parents=True, exist_ok=True)

WORKING_MODELS_PATH = REPORTS / 'working_hf_models.jsonl'
SEARCH_RESULTS_PATH = REPORTS / 'hf_model_search.jsonl'

# Тестовый промпт для проверки
TEST_PROMPT = "A cute red cat sitting on a windowsill, sunlight, photorealistic, 4k"

# Популярные рабочие модели для начала
KNOWN_WORKING_MODELS = [
    "stabilityai/stable-diffusion-3-medium-diffusers",
    "stabilityai/stable-diffusion-3.5-medium", 
    "stabilityai/stable-diffusion-xl-base-1.0",
    "stabilityai/sdxl-turbo",
    "runwayml/stable-diffusion-v1-5",
    "CompVis/stable-diffusion-v1-4",
    "SG161222/Realistic_Vision_V5.1_noVAE",
    "Lykon/dreamshaper-7",
    "black-forest-labs/FLUX.1-dev",
    "black-forest-labs/FLUX.1-schnell"
]

async def test_model_inference(session: aiohttp.ClientSession, model_id: str, timeout: int = 30) -> dict:
    """Тестирует модель через Inference API"""
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}" if HF_TOKEN else "",
        "Accept": "application/json"
    }
    
    payload = {"inputs": TEST_PROMPT}
    
    start_time = time.time()
    try:
        async with session.post(url, json=payload, headers=headers, timeout=timeout) as resp:
            elapsed = int((time.time() - start_time) * 1000)
            content_type = resp.headers.get('content-type', '')
            
            if resp.status == 200:
                if content_type.startswith('image/'):
                    return {
                        'model_id': model_id,
                        'status': 'success',
                        'content_type': content_type,
                        'elapsed_ms': elapsed,
                        'error': None
                    }
                elif 'application/json' in content_type:
                    # Возможно, модель загружается
                    data = await resp.text()
                    if 'loading' in data.lower() or 'model' in data.lower():
                        return {
                            'model_id': model_id,
                            'status': 'loading',
                            'content_type': content_type,
                            'elapsed_ms': elapsed,
                            'error': 'Model is loading'
                        }
            
            # Обрабатываем ошибки
            try:
                error_data = await resp.text()
                if len(error_data) > 200:
                    error_data = error_data[:200] + "..."
            except:
                error_data = f"HTTP {resp.status}"
                
            return {
                'model_id': model_id,
                'status': 'error',
                'content_type': content_type,
                'elapsed_ms': elapsed,
                'error': error_data
            }
            
    except asyncio.TimeoutError:
        return {
            'model_id': model_id,
            'status': 'timeout',
            'content_type': None,
            'elapsed_ms': int((time.time() - start_time) * 1000),
            'error': 'Request timeout'
        }
    except Exception as e:
        return {
            'model_id': model_id,
            'status': 'exception',
            'content_type': None,
            'elapsed_ms': int((time.time() - start_time) * 1000),
            'error': str(e)
        }

async def search_models_by_tag(session: aiohttp.ClientSession, tag: str, limit: int = 50) -> list:
    """Ищет модели по тегу через HF API"""
    if not HF_TOKEN:
        print(f"⚠️ Нет токена для поиска по тегу '{tag}'")
        return []
    
    url = "https://huggingface.co/api/models"
    params = {
        "search": tag,
        "filter": "pipeline_tag:text-to-image",
        "limit": limit,
        "sort": "downloads"
    }
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return [model['id'] for model in data if 'id' in model]
            else:
                print(f"❌ Ошибка поиска: HTTP {resp.status}")
                return []
    except Exception as e:
        print(f"❌ Ошибка поиска моделей: {e}")
        return []

async def test_models_batch(model_ids: list, concurrency: int = 3, timeout: int = 30) -> list:
    """Тестирует группу моделей с ограниченной параллельностью"""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def test_with_semaphore(model_id: str):
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                return await test_model_inference(session, model_id, timeout)
    
    tasks = [test_with_semaphore(mid) for mid in model_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Фильтруем исключения
    valid_results = []
    for result in results:
        if isinstance(result, dict):
            valid_results.append(result)
        else:
            print(f"⚠️ Исключение при тестировании: {result}")
    
    return valid_results

async def main():
    """Основная функция поиска рабочих моделей"""
    print("🔍 ПОИСК РАБОЧИХ МОДЕЛЕЙ TEXT-TO-IMAGE")
    print("=" * 60)
    
    if not HF_TOKEN:
        print("⚠️ HF_API_TOKEN не найден - ограниченная функциональность")
    else:
        print(f"✅ Токен найден: {HF_TOKEN[:10]}...")
    
    all_results = []
    working_models = []
    
    # 1. Тестируем известные рабочие модели
    print(f"\n🚀 Тестируем {len(KNOWN_WORKING_MODELS)} известных моделей...")
    results = await test_models_batch(KNOWN_WORKING_MODELS, concurrency=3, timeout=30)
    
    for result in results:
        all_results.append(result)
        if result['status'] == 'success':
            working_models.append(result['model_id'])
            print(f"✅ {result['model_id']} - РАБОТАЕТ! ({result['elapsed_ms']}ms)")
        elif result['status'] == 'loading':
            print(f"⏳ {result['model_id']} - загружается...")
        else:
            print(f"❌ {result['model_id']} - {result['error']}")
    
    # 2. Ищем новые модели по тегам
    if HF_TOKEN:
        print(f"\n🔍 Ищем новые модели по тегам...")
        search_tags = ["stable-diffusion", "sdxl", "flux", "realistic", "anime"]
        
        for tag in search_tags:
            print(f"   Поиск: {tag}")
            new_models = await search_models_by_tag(session=aiohttp.ClientSession(), tag=tag, limit=20)
            
            # Фильтруем уже протестированные
            new_models = [m for m in new_models if m not in [r['model_id'] for r in all_results]]
            
            if new_models:
                print(f"   Найдено новых: {len(new_models)}")
                results = await test_models_batch(new_models[:10], concurrency=2, timeout=20)
                
                for result in results:
                    all_results.append(result)
                    if result['status'] == 'success':
                        working_models.append(result['model_id'])
                        print(f"✅ {result['model_id']} - НОВАЯ РАБОЧАЯ! ({result['elapsed_ms']}ms)")
    
    # 3. Сохраняем результаты
    print(f"\n💾 Сохраняем результаты...")
    
    # Все результаты
    with open(SEARCH_RESULTS_PATH, 'w', encoding='utf-8') as f:
        for result in all_results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    # Только рабочие модели
    with open(WORKING_MODELS_PATH, 'w', encoding='utf-8') as f:
        for model_id in working_models:
            f.write(json.dumps({'model_id': model_id, 'found_at': datetime.now().isoformat()}, ensure_ascii=False) + '\n')
    
    # 4. Финальная статистика
    print(f"\n📊 РЕЗУЛЬТАТЫ ПОИСКА:")
    print(f"   🔍 Всего протестировано: {len(all_results)}")
    print(f"   ✅ Рабочих моделей: {len(working_models)}")
    print(f"   📁 Все результаты: {SEARCH_RESULTS_PATH}")
    print(f"   🎯 Рабочие модели: {WORKING_MODELS_PATH}")
    
    if working_models:
        print(f"\n🎉 НАЙДЕНЫ РАБОЧИЕ МОДЕЛИ:")
        for i, model in enumerate(working_models, 1):
            print(f"   {i}. {model}")
    else:
        print(f"\n⚠️ Рабочие модели не найдены. Проверьте токен и настройки.")
    
    return len(working_models) > 0

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Поиск прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
