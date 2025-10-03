#!/usr/bin/env python3
"""
Тест выбора голосов ElevenLabs
"""
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from backend.voice.tts import TextToSpeech

async def test_voice_selection():
    """Тестируем выбор голосов"""
    
    print("🎤 ТЕСТ ВЫБОРА ГОЛОСОВ ELEVENLABS")
    print("=" * 50)
    
    # Проверяем настройки
    print("📋 НАСТРОЙКИ:")
    print(f"ELEVEN_VOICE_ID_MALE: {os.getenv('ELEVEN_VOICE_ID_MALE')}")
    print(f"ELEVEN_VOICE_ID_FEMALE: {os.getenv('ELEVEN_VOICE_ID_FEMALE')}")
    print(f"ELEVEN_VOICE_ID: {os.getenv('ELEVEN_VOICE_ID')}")
    print()
    
    # Создаем TTS
    tts = TextToSpeech()
    
    # Тестируем выбор голосов
    test_cases = [
        {"gender": "male", "lang": "ru"},
        {"gender": "female", "lang": "ru"},
        {"gender": "male", "lang": "en"},
        {"gender": "female", "lang": "en"},
    ]
    
    for i, voice_config in enumerate(test_cases, 1):
        print(f"🧪 ТЕСТ {i}: {voice_config}")
        
        # Получаем voice_id
        voice_id = tts._map_voice_id_by_gender(voice_config)
        print(f"   → Voice ID: {voice_id}")
        
        if voice_id:
            print(f"   ✅ Успешно выбран голос")
        else:
            print(f"   ❌ Голос не найден")
        print()

if __name__ == "__main__":
    asyncio.run(test_voice_selection())
