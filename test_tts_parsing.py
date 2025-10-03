#!/usr/bin/env python3
"""
Тест парсинга TTS JSON - проверяем что парсер извлекает только текст из поля 'text'
"""

import sys
import os
sys.path.append('backend')

from backend.utils.robust_json_parser import parse_speak_json
from backend.llm.openrouter import OpenRouterClient
from backend.config import Config

async def test_tts_parsing():
    """Тестируем парсинг TTS JSON"""
    
    print("🎤 ТЕСТ ПАРСИНГА TTS JSON")
    print("=" * 50)
    
    # 1. Создаем запрос к модели
    print("1. Создаем запрос к модели...")
    
    config = Config()
    client = OpenRouterClient(config)
    
    prompt = """Ты — Чатумба, умный AI-друг в групповом чате.

🎤 ОЗВУЧКА (TTS):
Если пользователь просит озвучить (слова: "озвучь", "голосом", "голосовое"), добавь В КОНЕЦ ответа отдельной строкой SPEAK!{...} с параметрами озвучки.
ВАЖНО: В поле "text" укажи ТОЛЬКО тот текст, который нужно озвучить! Не весь ответ!
Пример (эмоциональная женская русская речь):
SPEAK!{"speak": true, "text": "Привет! Как дела?", "tts": {"provider": "elevenlabs", "voice": {"gender": "female", "lang": "ru"}, "model_id": "eleven_multilingual_v2", "output_format": "mp3_44100_128", "stability": 0.25, "similarity_boost": 0.8, "style_exaggeration": 0.6, "use_speaker_boost": true}}

ОБЯЗАТЕЛЬНО: Если пользователь просит спеть песню, добавь SPEAK! JSON в конец ответа!

Пользователь просит: "спой песню про трейдинг" """
    
    try:
        # Генерируем ответ от модели
        print("2. Генерируем ответ от модели...")
        response = await client.generate_response(
            prompt=prompt,
            use_memory=False,
            max_tokens=1000,
            temperature=0.7
        )
        
        print(f"✅ Ответ получен: {len(response)} символов")
        print(f"📝 Ответ:\n{response}")
        print("\n" + "=" * 50)
        
        # 2. Парсим SPEAK! JSON
        print("3. Парсим SPEAK! JSON...")
        speak_json = parse_speak_json(response)
        
        print(f"📊 Результат парсинга: {speak_json}")
        print(f"🔑 Ключи в JSON: {list(speak_json.keys())}")
        
        # 3. Проверяем наличие поля 'text'
        if 'text' in speak_json:
            text_to_speak = speak_json['text']
            print(f"✅ Поле 'text' найдено!")
            print(f"🎤 Текст для озвучки: {text_to_speak}")
            print(f"📏 Длина текста: {len(text_to_speak)} символов")
            
            # 4. Проверяем что это НЕ весь ответ
            if text_to_speak in response:
                print("⚠️  ВНИМАНИЕ: Текст для озвучки содержится в полном ответе")
                if len(text_to_speak) < len(response) * 0.8:
                    print("✅ ХОРОШО: Текст для озвучки значительно короче полного ответа")
                else:
                    print("❌ ПЛОХО: Текст для озвучки почти равен полному ответу")
            else:
                print("❌ ОШИБКА: Текст для озвучки НЕ содержится в полном ответе")
                
        else:
            print("❌ Поле 'text' НЕ найдено!")
            print("🔍 Пробуем извлечь текст другим способом...")
            
            # Fallback: ищем текст вручную
            import re
            text_match = re.search(r'"text":\s*"([^"]*)"', response)
            if text_match:
                fallback_text = text_match.group(1)
                print(f"🔧 Fallback текст: {fallback_text}")
            else:
                print("❌ Fallback тоже не сработал")
        
        print("\n" + "=" * 50)
        print("🎯 ИТОГ ТЕСТА:")
        
        if 'text' in speak_json and len(speak_json['text']) < len(response) * 0.8:
            print("✅ УСПЕХ: Парсер работает правильно!")
            print("✅ Текст для озвучки извлечен корректно!")
            print("✅ Длина текста для озвучки меньше полного ответа!")
        else:
            print("❌ ПРОВАЛ: Парсер работает неправильно!")
            print("❌ Нужно исправлять парсер!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tts_parsing())
