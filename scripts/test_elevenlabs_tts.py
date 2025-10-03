#!/usr/bin/env python3
"""
Скрипт для тестирования ElevenLabs TTS
"""

import os
import sys
import json
from pathlib import Path

# Добавляем путь к проекту
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.voice.tts import TextToSpeech

def test_elevenlabs_tts():
    """Тестирует ElevenLabs TTS"""
    print("🎤 Тестирование ElevenLabs TTS...")
    
    # Загружаем переменные окружения
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Проверяем кэшированные голоса
    voices_file = PROJECT_ROOT / 'data' / 'eleven_voices_ru.json'
    if voices_file.exists():
        with open(voices_file, 'r', encoding='utf-8') as f:
            voices = json.load(f)
            print(f"📁 Найдено {len(voices)} кэшированных голосов:")
            for voice in voices:
                print(f"  - {voice.get('name')} ({voice.get('voice_id')}) - {voice.get('gender')}")
    else:
        print("❌ Файл с голосами не найден!")
        return
    
    # Создаем TTS
    try:
        tts = TextToSpeech()
        print(f"✅ TTS инициализирован")
        print(f"🎤 ElevenLabs voice_id: {tts.eleven_voice_id}")
        print(f"🎤 ElevenLabs модель: {tts.eleven_model_id}")
        
        # Тестируем озвучку
        test_text = "Привет! Это тест ElevenLabs TTS. Работает отлично!"
        print(f"📝 Тестируем текст: {test_text}")
        
        # Создаем аудио
        audio_path = tts.text_to_speech_with_params(
            test_text, 
            {
                "provider": "elevenlabs",
                "voice": {"gender": "female", "lang": "ru"},
                "model_id": "eleven_multilingual_v2",
                "output_format": "mp3_44100_128",
                "stability": 0.25,
                "similarity_boost": 0.8,
                "style_exaggeration": 0.6
            }
        )
        
        if audio_path and os.path.exists(audio_path):
            print(f"✅ Аудио создано: {audio_path}")
            print(f"📊 Размер файла: {os.path.getsize(audio_path)} байт")
            
            # Показываем содержимое папки temp
            temp_dir = PROJECT_ROOT / 'temp'
            if temp_dir.exists():
                print(f"📁 Файлы в temp/:")
                for file in temp_dir.glob('*'):
                    if file.is_file():
                        print(f"  - {file.name} ({os.path.getsize(file)} байт)")
        else:
            print(f"❌ Аудио не создано: {audio_path}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_elevenlabs_tts()
