#!/usr/bin/env python3
"""
Тест Prompt Caching для Grok 4 Fast
"""

import asyncio
import aiohttp
import json
import os
import time
from dotenv import load_dotenv

load_dotenv('/root/IKAR-ASSISTANT/.env')

async def test_prompt_cache():
    """Тестируем кэширование промптов"""
    
    api_key = os.getenv('OPENROUTER_API_KEY_PAID')
    if not api_key:
        print("❌ Платный ключ не найден!")
        return
    
    print(f"🔑 Используем ключ: {api_key[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/ikar",
        "X-Title": "IKAR Cache Test"
    }
    
    # Большой системный промпт для кэширования
    system_prompt = """Ты — Икар Икарыч, цифровой сотрудник компании «ИКАР». 

Компания работает в городе Шахты, Ростовская область. Основная специализация — автоматизация бизнеса: кассовая техника (ККМ), программные продукты (1С и СБИС), обслуживание и сопровождение.

У компании два офиса:
- Основной — г. Шахты, ул. Шевченко 76, 5-этажная «хрущёвка», 4-й подъезд (крайний справа), цокольный этаж, по коридору прямо до конца.
- Второй — бизнес-островок в деловом центре «Город Будущего», прямо напротив окошек налоговой.

КОНТАКТЫ КОМПАНИИ:
- Городской номер: +78636237037
- Касса: +7 919-880-59-99
- Ангелина: +7 988-998-07-00
- Игорь: +7 988-998-78-78
- Влад: +7 988-575-61-61

ЦЕНЫ НА КАССОВУЮ ТЕХНИКУ:
- Эвотор 5: 24,900 ₽ (без ФН), 38,000 ₽ (ФН 15 мес), 43,000 ₽ (под ключ)
- Эвотор 7.2: 29,900 ₽ (без ФН), 43,000 ₽ (ФН 15 мес), 48,000 ₽ (под ключ)
- Атол Sigma 7: 21,500 ₽ (без ФН), 34,600 ₽ (ФН 15 мес), 39,600 ₽ (под ключ)

ИТ-УСЛУГИ:
- Обновление 1С (до 3 версий): 1,300 ₽
- Удалённое подключение: 650 ₽
- Обновление 1С + удалёнка: 2,600 ₽

Отвечай профессионально и по делу!"""
    
    print("🧪 ТЕСТ 1: Первый запрос (Cache Write)")
    print("=" * 50)
    
    # Первый запрос - должен создать кэш
    payload1 = {
        "model": "x-ai/grok-4-fast",
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
                "metadata": {
                    "cache": True
                }
            },
            {
                "role": "user",
                "content": "Привет! Расскажи про цены на кассы Эвотор."
            }
        ],
        "max_tokens": 200,
        "temperature": 0.3
    }
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload1,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            
            first_time = time.time() - start_time
            
            if response.status == 200:
                data1 = await response.json()
                
                if 'usage' in data1:
                    usage1 = data1['usage']
                    print(f"📈 ТОКЕНЫ (первый запрос):")
                    print(f"   Входные: {usage1.get('prompt_tokens', 0):,}")
                    print(f"   Выходные: {usage1.get('completion_tokens', 0):,}")
                    print(f"   Всего: {usage1.get('total_tokens', 0):,}")
                    print(f"⏱️ Время: {first_time:.2f} сек")
                
                if 'choices' in data1 and data1['choices']:
                    answer1 = data1['choices'][0]['message']['content']
                    print(f"🤖 ОТВЕТ: {answer1[:100]}...")
                
                print("\n🧪 ТЕСТ 2: Второй запрос (Cache Read)")
                print("=" * 50)
                
                # Второй запрос - должен использовать кэш
                payload2 = {
                    "model": "x-ai/grok-4-fast",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt,  # Тот же промпт
                            "metadata": {
                                "cache": True
                            }
                        },
                        {
                            "role": "user",
                            "content": "А что с ценами на Атол?"
                        }
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3
                }
                
                start_time = time.time()
                
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload2,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response2:
                    
                    second_time = time.time() - start_time
                    
                    if response2.status == 200:
                        data2 = await response2.json()
                        
                        if 'usage' in data2:
                            usage2 = data2['usage']
                            print(f"📈 ТОКЕНЫ (второй запрос):")
                            print(f"   Входные: {usage2.get('prompt_tokens', 0):,}")
                            print(f"   Выходные: {usage2.get('completion_tokens', 0):,}")
                            print(f"   Всего: {usage2.get('total_tokens', 0):,}")
                            print(f"⏱️ Время: {second_time:.2f} сек")
                        
                        if 'choices' in data2 and data2['choices']:
                            answer2 = data2['choices'][0]['message']['content']
                            print(f"🤖 ОТВЕТ: {answer2[:100]}...")
                        
                        print("\n📊 АНАЛИЗ КЭША:")
                        print("=" * 50)
                        
                        # Сравниваем токены
                        first_input = usage1.get('prompt_tokens', 0)
                        second_input = usage2.get('prompt_tokens', 0)
                        
                        if second_input < first_input:
                            saved_tokens = first_input - second_input
                            print(f"✅ КЭШ РАБОТАЕТ!")
                            print(f"   Сэкономлено токенов: {saved_tokens:,}")
                            print(f"   Экономия: {saved_tokens/first_input*100:.1f}%")
                        else:
                            print(f"❌ КЭШ НЕ РАБОТАЕТ")
                            print(f"   Токены одинаковые: {first_input:,}")
                        
                        # Сравниваем время
                        if second_time < first_time:
                            print(f"⚡ Ускорение: {first_time/second_time:.1f}x")
                        else:
                            print(f"⏱️ Время примерно одинаковое")
                            
                    else:
                        text2 = await response2.text()
                        print(f"❌ Ошибка второго запроса {response2.status}: {text2}")
            else:
                text1 = await response.text()
                print(f"❌ Ошибка первого запроса {response.status}: {text1}")

if __name__ == "__main__":
    asyncio.run(test_prompt_cache())
