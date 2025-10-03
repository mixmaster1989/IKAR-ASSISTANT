#!/usr/bin/env python3
"""
Скрипт для проверки ключей ElevenLabs и получения озвучки
"""

import os
import sys
import requests
import json
from pathlib import Path

def load_env_file():
    """Читает .env файл и возвращает словарь с переменными"""
    env_path = Path(__file__).parent / '.env'
    env_vars = {}
    
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        return None
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        print("✅ .env файл успешно прочитан")
        return env_vars
    except Exception as e:
        print(f"❌ Ошибка при чтении .env файла: {e}")
        return None

def test_elevenlabs_api(api_key):
    """Тестирует API ElevenLabs"""
    base_url = "https://api.elevenlabs.io"
    
    # Проверяем доступные голоса
    print("\n🔍 Проверяем доступные голоса...")
    try:
        response = requests.get(
            f"{base_url}/v1/voices",
            headers={"xi-api-key": api_key}
        )
        
        if response.status_code == 200:
            voices = response.json()
            print(f"✅ Получено {len(voices.get('voices', []))} голосов")
            
            # Ищем русскоязычный голос
            russian_voices = []
            for voice in voices.get('voices', []):
                if 'russian' in voice.get('name', '').lower() or 'ru' in voice.get('name', '').lower():
                    russian_voices.append(voice)
            
            if russian_voices:
                print("🇷🇺 Найдены русскоязычные голоса:")
                for voice in russian_voices[:3]:  # Показываем первые 3
                    print(f"  - {voice['name']} (ID: {voice['voice_id']})")
                voice_id = russian_voices[0]['voice_id']
            else:
                print("⚠️ Русскоязычные голоса не найдены, используем первый доступный")
                voice_id = voices['voices'][0]['voice_id']
                print(f"  - {voices['voices'][0]['name']} (ID: {voice_id})")
            
            return voice_id
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка при проверке голосов: {e}")
        return None

def generate_speech(api_key, voice_id, text):
    """Генерирует озвучку текста"""
    base_url = "https://api.elevenlabs.io"
    
    print(f"\n🎤 Генерируем озвучку для текста: '{text}'")
    
    try:
        response = requests.post(
            f"{base_url}/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
        )
        
        if response.status_code == 200:
            # Сохраняем аудио файл
            audio_path = Path(__file__).parent / "test_audio.mp3"
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Озвучка успешно создана: {audio_path}")
            print(f"📁 Размер файла: {len(response.content)} байт")
            return True
        else:
            print(f"❌ Ошибка генерации речи: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при генерации речи: {e}")
        return False

def main():
    print("🚀 Тестирование ElevenLabs API")
    print("=" * 40)
    
    # Загружаем переменные окружения
    env_vars = load_env_file()
    if not env_vars:
        return
    
    # Проверяем наличие API ключа
    api_key = env_vars.get('ELEVEN_API')
    if not api_key:
        print("❌ ELEVEN_API не найден в .env файле!")
        return
    
    print(f"✅ API ключ найден: {api_key[:10]}...")
    
    # Тестируем API
    voice_id = test_elevenlabs_api(api_key)
    if not voice_id:
        return
    
    # Генерируем озвучку
    test_text = "Привет мир как дела"  # 5 слов на русском
    success = generate_speech(api_key, voice_id, test_text)
    
    if success:
        print("\n🎉 Тест завершен успешно!")
    else:
        print("\n💥 Тест завершен с ошибками!")

if __name__ == "__main__":
    main()
