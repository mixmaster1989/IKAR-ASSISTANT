#!/usr/bin/env python3
"""
Тест полного цикла TTS - от парсинга до отправки в ElevenLabs (заглушка)
"""

import sys
import os
sys.path.append('backend')

from backend.utils.robust_json_parser import parse_speak_json
from backend.llm.openrouter import OpenRouterClient
from backend.config import Config
import re

class MockElevenLabs:
    """Заглушка ElevenLabs для тестирования"""
    
    def __init__(self):
        self.calls = []
    
    def text_to_speech(self, text, **kwargs):
        """Заглушка TTS"""
        self.calls.append({
            'text': text,
            'kwargs': kwargs
        })
        print(f"🎤 ELEVENLABS ЗАГЛУШКА: Получен текст для озвучки")
        print(f"📝 Текст: {text[:100]}...")
        print(f"📏 Длина: {len(text)} символов")
        print(f"⚙️ Параметры: {kwargs}")
        return "/fake/path/audio.mp3"

async def test_full_tts_cycle():
    """Тестируем полный цикл TTS"""
    
    print("🎤 ТЕСТ ПОЛНОГО ЦИКЛА TTS")
    print("=" * 60)
    
    # 1. Создаем запрос к модели
    print("1. Создаем запрос к модели...")
    
    config = Config()
    client = OpenRouterClient(config)
    mock_elevenlabs = MockElevenLabs()
    
    prompt = """Ты — Чатумба, умный AI-друг в групповом чате.

🎤 ОЗВУЧКА (TTS):
Если пользователь просит озвучить (слова: "озвучь", "голосом", "голосовое"), добавь В КОНЕЦ ответа отдельной строкой SPEAK!{...} с параметрами озвучки.
ВАЖНО: В поле "text" укажи ТОЛЬКО тот текст, который нужно озвучить! Не весь ответ!
Пример (эмоциональная женская русская речь):
SPEAK!{"speak": true, "text": "Привет! Как дела?", "tts": {"provider": "elevenlabs", "voice": {"gender": "female", "lang": "ru"}, "model_id": "eleven_multilingual_v2", "output_format": "mp3_44100_128", "stability": 0.25, "similarity_boost": 0.8, "style_exaggeration": 0.6, "use_speaker_boost": true}}

ОБЯЗАТЕЛЬНО: Если пользователь просит спеть песню, добавь SPEAK! JSON в конец ответа!

Пользователь просит: "спой песню про трейдинг" """
    
    try:
        # 2. Генерируем ответ от модели
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
        speak_json = parse_speak_json(response)
        
        print(f"📊 Результат парсинга: {speak_json}")
        print(f"🔑 Ключи в JSON: {list(speak_json.keys())}")
        
        # 4. Извлекаем текст для озвучки
        text_to_speak = None
        
        if 'text' in speak_json:
            text_to_speak = speak_json['text']
            print(f"✅ Поле 'text' найдено в парсере!")
        else:
            print("⚠️ Поле 'text' не найдено в парсере, используем fallback...")
            # Fallback: ищем текст вручную
            text_match = re.search(r'"text":\s*"([^"]*)"', response)
            if text_match:
                text_to_speak = text_match.group(1)
                print(f"🔧 Fallback текст найден!")
            else:
                print("❌ Fallback тоже не сработал!")
                return
        
        print(f"🎤 Текст для озвучки: {text_to_speak}")
        print(f"📏 Длина текста: {len(text_to_speak)} символов")
        
        # 5. Проверяем что это НЕ весь ответ
        if text_to_speak in response:
            print("✅ Текст для озвучки содержится в полном ответе")
            if len(text_to_speak) < len(response) * 0.8:
                print("✅ ХОРОШО: Текст для озвучки значительно короче полного ответа")
                success = True
            else:
                print("❌ ПЛОХО: Текст для озвучки почти равен полному ответу")
                success = False
        else:
            print("❌ ОШИБКА: Текст для озвучки НЕ содержится в полном ответе")
            success = False
        
        # 6. Отправляем в ElevenLabs (заглушка)
        print("\n4. Отправляем в ElevenLabs (заглушка)...")
        
        # Извлекаем параметры TTS
        tts_params = speak_json.get('tts', {})
        if not tts_params and 'text' not in speak_json:
            # Если парсер не сработал, используем fallback параметры
            tts_params = {
                'provider': 'elevenlabs',
                'voice': {'gender': 'male', 'lang': 'ru'},
                'model_id': 'eleven_multilingual_v2',
                'output_format': 'mp3_44100_128',
                'stability': 0.5,
                'similarity_boost': 0.75,
                'style_exaggeration': 0.8,
                'use_speaker_boost': True
            }
            print("🔧 Используем fallback параметры TTS")
        
        audio_path = mock_elevenlabs.text_to_speech(text_to_speak, **tts_params)
        
        print(f"✅ Аудио создано: {audio_path}")
        print(f"📊 Количество вызовов ElevenLabs: {len(mock_elevenlabs.calls)}")
        
        # 7. Итоговый результат
        print("\n" + "=" * 60)
        print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        
        if success and len(mock_elevenlabs.calls) == 1:
            print("✅ УСПЕХ: Полный цикл TTS работает правильно!")
            print("✅ Текст для озвучки извлечен корректно!")
            print("✅ ElevenLabs получил только нужный текст!")
            print("✅ Длина текста для озвучки меньше полного ответа!")
        else:
            print("❌ ПРОВАЛ: Есть проблемы в цикле TTS!")
            if not success:
                print("❌ Проблема с извлечением текста!")
            if len(mock_elevenlabs.calls) != 1:
                print("❌ Проблема с вызовом ElevenLabs!")
        
        # 8. Детали вызова ElevenLabs
        if mock_elevenlabs.calls:
            call = mock_elevenlabs.calls[0]
            print(f"\n📋 ДЕТАЛИ ВЫЗОВА ELEVENLABS:")
            print(f"📝 Текст: {call['text'][:100]}...")
            print(f"📏 Длина: {len(call['text'])} символов")
            print(f"⚙️ Параметры: {call['kwargs']}")
            
            # Проверяем что в ElevenLabs попал только текст песни
            if "спой песню" not in call['text'].lower() and "как вам" not in call['text'].lower():
                print("✅ ХОРОШО: В ElevenLabs попал только текст песни!")
            else:
                print("❌ ПЛОХО: В ElevenLabs попал лишний текст!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_full_tts_cycle())
