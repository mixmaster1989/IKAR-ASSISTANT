#!/usr/bin/env python3
"""
Скрипт для циклического перебора ключей ElevenLabs
При ошибке на одном ключе автоматически переходит к следующему
"""

import os
import sys
import requests
import json
import time
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
        return env_vars
    except Exception as e:
        print(f"❌ Ошибка при чтении .env файла: {e}")
        return None

def get_eleven_keys(env_vars):
    """Извлекает все ключи ElevenLabs из .env файла"""
    keys = []
    for key, value in env_vars.items():
        if key.startswith('ELEVEN_') and value.startswith('sk_'):
            keys.append((key, value))
    return keys

def test_single_key(api_key, key_name, test_text="Привет мир как дела"):
    """Тестирует один ключ API"""
    base_url = "https://api.elevenlabs.io"
    
    print(f"🔑 Тестируем ключ: {key_name}")
    
    try:
        # Сначала получаем список голосов
        response = requests.get(
            f"{base_url}/v1/voices",
            headers={"xi-api-key": api_key},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения голосов: {response.status_code} - {response.text[:100]}")
            return False, f"HTTP {response.status_code}"
        
        voices = response.json()
        if not voices.get('voices'):
            print("❌ Нет доступных голосов")
            return False, "No voices"
        
        # Берем первый доступный голос
        voice_id = voices['voices'][0]['voice_id']
        voice_name = voices['voices'][0]['name']
        print(f"🎤 Используем голос: {voice_name} (ID: {voice_id})")
        
        # Генерируем речь
        response = requests.post(
            f"{base_url}/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "text": test_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            # Сохраняем аудио файл
            audio_path = Path(__file__).parent / f"audio_{key_name}.mp3"
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Успех! Аудио сохранено: {audio_path}")
            print(f"📁 Размер файла: {len(response.content)} байт")
            return True, "Success"
        else:
            print(f"❌ Ошибка генерации речи: {response.status_code} - {response.text[:100]}")
            return False, f"TTS HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        print("⏰ Таймаут запроса")
        return False, "Timeout"
    except requests.exceptions.RequestException as e:
        print(f"🌐 Ошибка сети: {e}")
        return False, f"Network: {str(e)[:50]}"
    except Exception as e:
        print(f"💥 Неожиданная ошибка: {e}")
        return False, f"Exception: {str(e)[:50]}"

def cycle_through_keys(keys, cycles=5, pause_between_cycles=10):
    """Циклически перебирает все ключи"""
    print(f"🚀 Начинаем циклический перебор {len(keys)} ключей")
    print(f"📊 Всего циклов: {cycles}, пауза между циклами: {pause_between_cycles} сек")
    print("=" * 60)
    
    for cycle in range(1, cycles + 1):
        print(f"\n🔄 ЦИКЛ {cycle}/{cycles}")
        print("-" * 40)
        
        successful_keys = 0
        failed_keys = 0
        
        for i, (key_name, api_key) in enumerate(keys, 1):
            print(f"\n[{i}/{len(keys)}] Ключ: {key_name}")
            success, error = test_single_key(api_key, key_name)
            
            if success:
                successful_keys += 1
                print(f"✅ Ключ {key_name} работает!")
            else:
                failed_keys += 1
                print(f"❌ Ключ {key_name} не работает: {error}")
                print("➡️ Переходим к следующему ключу...")
        
        print(f"\n📊 Итоги цикла {cycle}:")
        print(f"   ✅ Работающих ключей: {successful_keys}")
        print(f"   ❌ Не работающих ключей: {failed_keys}")
        
        if cycle < cycles:
            print(f"\n⏳ Пауза {pause_between_cycles} секунд перед следующим циклом...")
            time.sleep(pause_between_cycles)
    
    print(f"\n🎉 Все {cycles} циклов завершены!")

def main():
    print("🔄 Циклический тест ключей ElevenLabs")
    print("=" * 50)
    
    # Загружаем переменные окружения
    env_vars = load_env_file()
    if not env_vars:
        return
    
    # Получаем все ключи ElevenLabs
    keys = get_eleven_keys(env_vars)
    if not keys:
        print("❌ Ключи ElevenLabs не найдены в .env файле!")
        return
    
    print(f"🔑 Найдено ключей: {len(keys)}")
    for key_name, key_value in keys:
        print(f"   - {key_name}: {key_value[:15]}...")
    
    # Запускаем циклический перебор
    cycle_through_keys(keys, cycles=5, pause_between_cycles=10)

if __name__ == "__main__":
    main()
