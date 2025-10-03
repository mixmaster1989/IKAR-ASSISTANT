#!/usr/bin/env python3
"""
Скрипт для получения списка доступных голосов ElevenLabs
"""

import requests
import json
import os
from dotenv import load_dotenv

def get_elevenlabs_voices():
    """Получаем список голосов ElevenLabs"""
    
    # Загружаем .env файл
    load_dotenv('/root/IKAR/.env')
    
    # Получаем API ключ
    api_key = os.getenv('ELEVEN_API')
    if not api_key:
        print("❌ API ключ ELEVEN_API не найден в .env файле")
        return
    
    print("🎤 Получаем список голосов ElevenLabs...")
    print(f"🔑 Используем ключ: {api_key[:10]}...")
    
    # Запрос к API
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "xi-api-key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            voices = data.get('voices', [])
            
            print(f"✅ Получено {len(voices)} голосов")
            print("\n" + "="*80)
            
            # Ищем русские голоса
            russian_voices = []
            male_voices = []
            female_voices = []
            
            for voice in voices:
                voice_id = voice.get('voice_id')
                name = voice.get('name', 'Unknown')
                category = voice.get('category', 'Unknown')
                description = voice.get('description', '')
                labels = voice.get('labels', {})
                
                # Проверяем на русский язык
                if 'ru' in labels.get('language', '').lower() or 'russian' in labels.get('language', '').lower():
                    russian_voices.append(voice)
                
                # Проверяем пол
                gender = labels.get('gender', '').lower()
                if gender == 'male':
                    male_voices.append(voice)
                elif gender == 'female':
                    female_voices.append(voice)
                
                print(f"🎤 {name}")
                print(f"   ID: {voice_id}")
                print(f"   Категория: {category}")
                print(f"   Описание: {description}")
                print(f"   Метки: {labels}")
                print("-" * 40)
            
            print("\n" + "="*80)
            print("🇷🇺 РУССКИЕ ГОЛОСА:")
            if russian_voices:
                for voice in russian_voices:
                    print(f"✅ {voice['name']} - {voice['voice_id']}")
            else:
                print("❌ Русские голоса не найдены")
            
            print("\n" + "="*80)
            print("👨 МУЖСКИЕ ГОЛОСА:")
            for voice in male_voices[:5]:  # Показываем первые 5
                print(f"✅ {voice['name']} - {voice['voice_id']}")
            
            print("\n" + "="*80)
            print("👩 ЖЕНСКИЕ ГОЛОСА:")
            for voice in female_voices[:5]:  # Показываем первые 5
                print(f"✅ {voice['name']} - {voice['voice_id']}")
            
            # Сохраняем в файл
            with open('/root/IKAR/elevenlabs_voices.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Данные сохранены в /root/IKAR/elevenlabs_voices.json")
            
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    get_elevenlabs_voices()
