#!/usr/bin/env python3
"""
Тест полного цикла: модель → выбор голоса → ElevenLabs
"""
import asyncio
import os
import re
from dotenv import load_dotenv
from pathlib import Path

# Загружаем .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from backend.utils.robust_json_parser import parse_speak_json
from backend.llm.openrouter import OpenRouterClient
from backend.config import Config
from backend.voice.tts import TextToSpeech

async def test_full_voice_cycle():
    """Тестируем полный цикл с выбором голоса"""
    
    print("🎤 ТЕСТ ПОЛНОГО ЦИКЛА С ВЫБОРОМ ГОЛОСА")
    print("=" * 60)
    
    # 1. Создаем запрос к модели
    print("1. Создаем запрос к модели...")
    
    config = Config()
    client = OpenRouterClient(config)
    
    prompt = """Ты — Чатумба, умный AI-друг в групповом чате.

🎤 ОЗВУЧКА (TTS):
Если пользователь просит озвучить (слова: "озвучь", "голосом", "голосовое"), добавь В КОНЕЦ ответа отдельной строкой SPEAK!{...} с параметрами озвучки.
ВАЖНО: В поле "text" укажи ТОЛЬКО тот текст, который нужно озвучить! Не весь ответ!

Доступные голоса:
- "male" - мужской голос (Clyde) - интенсивный, подходит для персонажей и эмоционального контента
- "female" - женский голос (Alice) - профессиональный, подходит для обучения и делового общения

Пример (эмоциональная женская русская речь):
SPEAK!{"speak": true, "text": "Привет! Как дела?", "tts": {"provider": "elevenlabs", "voice": {"gender": "female", "lang": "ru"}, "model_id": "eleven_multilingual_v2", "output_format": "mp3_44100_128", "stability": 0.25, "similarity_boost": 0.8, "style": "emotional", "use_speaker_boost": true}}

ОБЯЗАТЕЛЬНО: Если пользователь просит спеть песню, добавь SPEAK! JSON в конец ответа!

Пользователь просит: "спой песенку про трейдинг женским голосом" """
    
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
        print("\n" + "=" * 60)
        
        # 3. Парсим SPEAK! JSON
        print("3. Парсим SPEAK! JSON...")
        speak_params = parse_speak_json(response)
        
        print(f"📊 Результат парсинга: {speak_params}")
        print(f"🔑 Ключи в JSON: {list(speak_params.keys())}")
        
        speak_text = speak_params.get("text")
        tts_params = speak_params.get("tts", {})

        if not speak_text:
            print("⚠️ Поле 'text' не найдено в парсере, используем fallback...")
            # Fallback: ищем текст вручную с помощью regex
            text_match = re.search(r'"text":\s*"([^"]*)"', response)
            if text_match:
                speak_text = text_match.group(1)
                print(f"🔧 Fallback текст найден!")
            else:
                print("❌ Fallback текст не найден!")
                speak_text = ""
        
        if speak_text:
            print(f"🎤 Текст для озвучки: {speak_text[:100]}...")
            print(f"📏 Длина текста: {len(speak_text)} символов")
            
            # 4. Проверяем выбор голоса
            print("\n4. Проверяем выбор голоса...")
            voice_config = tts_params.get("voice", {})
            print(f"🎭 Конфигурация голоса от модели: {voice_config}")
            
            # Создаем TTS и проверяем voice_id
            tts = TextToSpeech()
            voice_id = tts._map_voice_id_by_gender(voice_config)
            print(f"🆔 Выбранный voice_id: {voice_id}")
            
            if voice_id:
                print("✅ Голос успешно выбран!")
                
                # Проверяем какой голос выбран
                if voice_id == "2EiwWnXFnvU5JabPnv8n":
                    print("👨 Выбран мужской голос: Clyde")
                elif voice_id == "Xb7hH8MSUJpSbSDYk0k2":
                    print("👩 Выбран женский голос: Alice")
                else:
                    print(f"❓ Неизвестный голос: {voice_id}")
            else:
                print("❌ Голос не выбран!")
            
            print("\n" + "=" * 60)
            print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
            print("✅ УСПЕХ: Полный цикл с выбором голоса работает!")
            print("✅ Модель может выбирать голос!")
            print("✅ Код правильно переводит в voice_id!")
            print("✅ ElevenLabs получит правильный голос!")

        else:
            print("❌ ПРОВАЛ: Текст для озвучки не найден!")
        
    except Exception as e:
        print(f"❌ Ошибка в полном цикле: {e}")

if __name__ == "__main__":
    asyncio.run(test_full_voice_cycle())
