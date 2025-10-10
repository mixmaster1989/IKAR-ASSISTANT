#!/usr/bin/env python3
"""
Тест для проверки всех ключей ElevenLabs
"""
import os
import requests
import json
from dotenv import load_dotenv

# Загружаем .env
load_dotenv("/root/IKAR-ASSISTANT/.env")

def test_elevenlabs_key(api_key, key_name):
    """Тестирует один ключ ElevenLabs"""
    print(f"\n🔑 Тестируем {key_name}: {api_key[:20]}...")
    
    # Проверяем баланс
    url = "https://api.elevenlabs.io/v1/user"
    headers = {"xi-api-key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            subscription = data.get('subscription', {})
            character_count = subscription.get('character_count', 0)
            character_limit = subscription.get('character_limit', 0)
            print(f"✅ {key_name}: {character_count}/{character_limit} символов")
            return True, character_count, character_limit
        else:
            print(f"❌ {key_name}: Ошибка {response.status_code} - {response.text[:100]}")
            return False, 0, 0
    except Exception as e:
        print(f"❌ {key_name}: Исключение - {e}")
        return False, 0, 0

def test_tts_generation(api_key, key_name):
    """Тестирует генерацию TTS"""
    print(f"\n🎤 Тестируем TTS для {key_name}...")
    
    url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": "Тест озвучки",
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            print(f"✅ {key_name}: TTS работает!")
            return True
        else:
            print(f"❌ {key_name}: TTS ошибка {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {key_name}: TTS исключение - {e}")
        return False

def main():
    print("🧪 ТЕСТ КЛЮЧЕЙ ELEVENLABS")
    print("=" * 50)
    
    # Собираем все ключи
    keys = []
    
    # Основной ключ
    main_key = os.getenv("ELEVEN_API") or os.getenv("ELEVEN_API_KEY")
    if main_key:
        keys.append(("ELEVEN_API", main_key))
    
    # Нумерованные ключи
    for i in range(2, 11):
        key = os.getenv(f"ELEVEN_API{i}")
        if key:
            keys.append((f"ELEVEN_API{i}", key))
    
    print(f"📊 Найдено ключей: {len(keys)}")
    
    working_keys = []
    
    # Тестируем каждый ключ
    for key_name, api_key in keys:
        # Проверяем баланс
        works, used, limit = test_elevenlabs_key(api_key, key_name)
        
        if works:
            # Тестируем TTS
            tts_works = test_tts_generation(api_key, key_name)
            if tts_works:
                working_keys.append((key_name, api_key, used, limit))
    
    # Итоги
    print("\n" + "=" * 50)
    print("📋 ИТОГИ:")
    print(f"✅ Рабочих ключей: {len(working_keys)}")
    print(f"❌ Нерабочих ключей: {len(keys) - len(working_keys)}")
    
    if working_keys:
        print("\n🎯 РАБОЧИЕ КЛЮЧИ:")
        for key_name, api_key, used, limit in working_keys:
            remaining = limit - used
            print(f"  {key_name}: {used}/{limit} символов (осталось: {remaining})")
    else:
        print("\n💀 НЕТ РАБОЧИХ КЛЮЧЕЙ!")

if __name__ == "__main__":
    main()
