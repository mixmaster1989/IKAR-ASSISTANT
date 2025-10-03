#!/usr/bin/env python3
"""
Упрощенный скрипт для получения голосов ElevenLabs
"""

import os
import json
import sys
from pathlib import Path
import requests

PROJECT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT / 'data'
DATA_DIR.mkdir(exist_ok=True)
ALL_PATH = DATA_DIR / 'eleven_voices.json'
RU_PATH = DATA_DIR / 'eleven_voices_ru.json'

def collect_keys():
    keys = []
    base = os.getenv('ELEVEN_API') or os.getenv('ELEVEN_API_KEY')
    if base:
        keys.append(base.strip())
    for i in range(2, 11):
        v = os.getenv(f'ELEVEN_API{i}')
        if v:
            keys.append(v.strip())
    return keys

def fetch_voices(keys):
    url = 'https://api.elevenlabs.io/v1/voices'
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Origin': 'https://elevenlabs.io',
        'Referer': 'https://elevenlabs.io/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site'
    }
    
    for key in keys:
        try:
            headers['xi-api-key'] = key
            print(f"Пробуем ключ: {key[:10]}...")
            
            resp = requests.get(url, headers=headers, timeout=30)
            print(f"Статус: {resp.status_code}")
            
            if resp.ok:
                data = resp.json()
                voices = data.get('voices', [])
                print(f"Получено голосов: {len(voices)}")
                return voices
            else:
                print(f"Ошибка: {resp.status_code} - {resp.text[:200]}")
                
        except Exception as e:
            print(f"Ошибка с ключом {key[:10]}...: {e}")
    
    return []

def is_russian_voice(voice):
    name = (voice.get('name') or '').lower()
    labels = voice.get('labels') or {}
    languages = voice.get('languages') or []
    
    # Проверяем различные варианты
    ru_indicators = ['russian', 'ru', 'русский', 'russia']
    
    for indicator in ru_indicators:
        if indicator in name:
            return True
        if indicator in str(labels).lower():
            return True
        if indicator in str(languages).lower():
            return True
    
    return False

def main():
    keys = collect_keys()
    if not keys:
        print("[ERR] Ключи ELEVEN_API не найдены в окружении")
        return
    
    print(f"Найдено ключей: {len(keys)}")
    
    voices = fetch_voices(keys)
    if not voices:
        print("[ERR] Не удалось получить голоса")
        return
    
    # Сохраняем все голоса
    ALL_PATH.write_text(json.dumps(voices, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"[OK] Все голоса сохранены: {ALL_PATH}")
    
    # Фильтруем русские
    ru_voices = [v for v in voices if is_russian_voice(v)]
    RU_PATH.write_text(json.dumps(ru_voices, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"[OK] Русские голоса сохранены: {RU_PATH} ({len(ru_voices)} голосов)")
    
    # Показываем русские голоса
    if ru_voices:
        print("\nРусские голоса:")
        for v in ru_voices:
            print(f"  - {v.get('name')} (ID: {v.get('voice_id')})")
    else:
        print("\nРусские голоса не найдены. Показываем все:")
        for v in voices[:5]:  # Первые 5
            print(f"  - {v.get('name')} (ID: {v.get('voice_id')})")

if __name__ == '__main__':
    main()
