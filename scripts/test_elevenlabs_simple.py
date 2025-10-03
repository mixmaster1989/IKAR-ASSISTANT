#!/usr/bin/env python3
"""
Упрощенный тест ElevenLabs TTS без torch
"""

import os
import sys
import json
import requests
from pathlib import Path

# Добавляем путь к проекту
PROJECT_ROOT = Path(__file__).resolve().parents[1]

def test_elevenlabs_direct():
    """Тестирует ElevenLabs TTS напрямую"""
    print("🎤 Тестирование ElevenLabs TTS напрямую...")
    
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
    
    # Выбираем женский голос
    female_voice = None
    for voice in voices:
        if voice.get('gender') == 'female':
            female_voice = voice
            break
    
    if not female_voice:
        female_voice = voices[0]  # Берем первый если женского нет
    
    print(f"🎤 Выбран голос: {female_voice.get('name')} ({female_voice.get('voice_id')})")
    
    # Получаем API ключи
    api_keys = []
    for i in range(1, 11):
        key = os.getenv(f'ELEVEN_API{i}' if i > 1 else 'ELEVEN_API')
        if key:
            api_keys.append(key)
    
    if not api_keys:
        print("❌ API ключи ElevenLabs не найдены!")
        return
    
    print(f"🔑 Найдено {len(api_keys)} API ключей")
    
    # Настройка прокси
    proxies = {}
    eleven_proxies = os.getenv('ELEVEN_PROXIES', '').strip()
    if eleven_proxies:
        proxies = {'https': eleven_proxies, 'http': eleven_proxies}
        print(f"🌐 Используем прокси: {eleven_proxies}")
    
    # Тестируем TTS
    test_text = "Привет! Это тест ElevenLabs TTS. Работает отлично!"
    print(f"📝 Тестируем текст: {test_text}")
    
    payload = {
        "text": test_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.25,
            "similarity_boost": 0.8,
            "style_exaggeration": 0.6,
            "use_speaker_boost": True
        },
        "output_format": "mp3_44100_128",
        "optimize_streaming_latency": 2
    }
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{female_voice.get('voice_id')}"
    
    for i, key in enumerate(api_keys):
        print(f"🔑 Пробуем ключ #{i+1}: {key[:10]}...")
        
        headers = {
            "xi-api-key": key, 
            "Content-Type": "application/json"
        }
        
        try:
            # Отключаем SSL проверку при использовании прокси
            verify_ssl = False  # Всегда отключаем SSL проверку
            
            resp = requests.post(
                url, 
                headers=headers, 
                data=json.dumps(payload).encode("utf-8"), 
                timeout=60, 
                proxies=proxies or None, 
                verify=verify_ssl
            )
            
            print(f"📡 Статус ответа: {resp.status_code}")
            
            if resp.ok and resp.content:
                # Сохраняем аудио
                output_path = PROJECT_ROOT / 'temp' / f'test_elevenlabs_{i+1}.mp3'
                output_path.parent.mkdir(exist_ok=True)
                
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                
                print(f"✅ Аудио создано: {output_path}")
                print(f"📊 Размер файла: {len(resp.content)} байт")
                print(f"🎉 ElevenLabs TTS работает!")
                return
            else:
                print(f"❌ Ошибка HTTP {resp.status_code}: {resp.text[:200]}")
                
        except Exception as e:
            print(f"❌ Ошибка с ключом #{i+1}: {e}")
    
    print("❌ Все ключи не работают!")

if __name__ == '__main__':
    test_elevenlabs_direct()
