#!/usr/bin/env python3
"""
Тест ElevenLabs TTS без прокси (прямое подключение)
"""

import os
import sys
import json
import asyncio
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

# Добавляем путь к проекту
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Загружаем переменные окружения
env_file = PROJECT_ROOT / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Загружен .env файл: {env_file}")
else:
    print(f"⚠️ .env файл не найден: {env_file}")

class ElevenLabsDirectTester:
    """Тестер ElevenLabs без прокси"""
    
    def __init__(self):
        self.api_keys = self._collect_api_keys()
        self.voices = self._load_voices()
        
    def _collect_api_keys(self) -> list:
        """Собирает ключи ElevenLabs из переменных окружения"""
        keys = []
        
        # Основные ключи
        base_key = os.getenv('ELEVEN_API') or os.getenv('ELEVEN_API_KEY')
        if base_key:
            keys.append(base_key.strip())
        
        # Дополнительные ключи
        for i in range(2, 11):
            key = os.getenv(f'ELEVEN_API{i}')
            if key:
                keys.append(key.strip())
        
        print(f"🔑 Найдено {len(keys)} ключей ElevenLabs")
        return keys
    
    def _load_voices(self) -> list:
        """Загружает кэшированные голоса"""
        voices_file = PROJECT_ROOT / 'data' / 'eleven_voices_ru.json'
        if voices_file.exists():
            with open(voices_file, 'r', encoding='utf-8') as f:
                voices = json.load(f)
                print(f"🎤 Загружено {len(voices)} русских голосов")
                return voices
        else:
            print("❌ Файл с голосами не найден!")
            return []
    
    async def test_elevenlabs_voices_direct(self):
        """Тестирует получение голосов ElevenLabs без прокси"""
        print("\n🎤 Тест 1: Получение голосов ElevenLabs (прямое подключение)")
        print("=" * 60)
        
        if not self.api_keys:
            print("❌ Нет ключей ElevenLabs!")
            return False
        
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_keys[0]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    print(f"📊 Статус: {response.status}")
                    
                    if response.status == 200:
                        voices_data = await response.json()
                        voices = voices_data.get('voices', [])
                        print(f"✅ Получено {len(voices)} голосов!")
                        
                        # Показываем первые 5 голосов
                        for i, voice in enumerate(voices[:5]):
                            print(f"  {i+1}. {voice.get('name')} ({voice.get('voice_id')}) - {voice.get('category')}")
                        
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Ошибка API: {response.status}")
                        print(f"📄 Ответ: {error_text[:200]}...")
                        return False
                        
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    async def test_elevenlabs_tts_direct(self):
        """Тестирует генерацию речи ElevenLabs без прокси"""
        print("\n🎤 Тест 2: Генерация речи ElevenLabs (прямое подключение)")
        print("=" * 60)
        
        if not self.api_keys or not self.voices:
            print("❌ Нет ключей или голосов!")
            return False
        
        # Выбираем женский голос
        female_voice = next((v for v in self.voices if v.get('gender') == 'female'), self.voices[0])
        print(f"🎤 Используем голос: {female_voice.get('name')} ({female_voice.get('voice_id')})")
        
        # Тестовый текст
        test_text = "Привет! Это тест ElevenLabs TTS без прокси. Работает отлично!"
        print(f"📝 Текст: {test_text}")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{female_voice.get('voice_id')}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_keys[0]
        }
        
        data = {
            "text": test_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    print(f"📊 Статус: {response.status}")
                    
                    if response.status == 200:
                        audio_data = await response.read()
                        print(f"✅ Сгенерировано аудио! Размер: {len(audio_data)} bytes")
                        
                        # Сохраняем аудио
                        os.makedirs("test_audio", exist_ok=True)
                        audio_file = f"test_audio/elevenlabs_direct_test.mp3"
                        with open(audio_file, "wb") as f:
                            f.write(audio_data)
                        print(f"💾 Аудио сохранено: {audio_file}")
                        
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Ошибка API: {response.status}")
                        print(f"📄 Ответ: {error_text[:200]}...")
                        return False
                        
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    async def test_multiple_voices(self):
        """Тестирует разные голоса"""
        print("\n🎤 Тест 3: Разные голоса ElevenLabs")
        print("=" * 60)
        
        if not self.api_keys or not self.voices:
            print("❌ Нет ключей или голосов!")
            return False
        
        # Тестируем первые 3 голоса
        test_voices = self.voices[:3]
        test_text = "Тест разных голосов"
        
        results = []
        
        for i, voice in enumerate(test_voices):
            print(f"\n🔍 Тестируем голос {i+1}/3: {voice.get('name')} ({voice.get('gender')})")
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{voice.get('voice_id')}",
                        headers={
                            "Accept": "audio/mpeg",
                            "Content-Type": "application/json",
                            "xi-api-key": self.api_keys[0]
                        },
                        json={
                            "text": test_text,
                            "model_id": "eleven_multilingual_v2"
                        },
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        if response.status == 200:
                            audio_data = await response.read()
                            print(f"✅ Голос {voice.get('name')} работает! Размер: {len(audio_data)} bytes")
                            results.append((voice.get('name'), True, len(audio_data)))
                        else:
                            print(f"❌ Голос {voice.get('name')} не работает: {response.status}")
                            results.append((voice.get('name'), False, 0))
                            
            except Exception as e:
                print(f"❌ Голос {voice.get('name')} ошибка: {e}")
                results.append((voice.get('name'), False, 0))
        
        # Результаты
        working_voices = [r for r in results if r[1]]
        print(f"\n📊 Результат: {len(working_voices)}/{len(test_voices)} голосов работают")
        
        for voice_name, success, size in results:
            status = "✅" if success else "❌"
            print(f"  {status} {voice_name} - {size} bytes")
        
        return len(working_voices) > 0
    
    async def test_performance(self):
        """Тестирует производительность"""
        print("\n🎤 Тест 4: Производительность ElevenLabs")
        print("=" * 60)
        
        if not self.api_keys or not self.voices:
            print("❌ Нет ключей или голосов!")
            return False
        
        import time
        
        voice = self.voices[0]
        test_text = "Тест производительности ElevenLabs"
        
        print(f"🎤 Голос: {voice.get('name')}")
        print(f"📝 Текст: {test_text}")
        
        # Измеряем время
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice.get('voice_id')}",
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": self.api_keys[0]
                    },
                    json={
                        "text": test_text,
                        "model_id": "eleven_multilingual_v2"
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        audio_data = await response.read()
                        end_time = time.time()
                        
                        duration = end_time - start_time
                        print(f"✅ Успешно! Время: {duration:.2f}s, Размер: {len(audio_data)} bytes")
                        print(f"📈 Скорость: {len(audio_data)/duration:.0f} bytes/sec")
                        
                        return True
                    else:
                        print(f"❌ Ошибка: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование ElevenLabs TTS (прямое подключение)")
    print("=" * 80)
    
    tester = ElevenLabsDirectTester()
    
    if not tester.api_keys:
        print("❌ Нет ключей ElevenLabs! Проверьте .env файл.")
        return
    
    if not tester.voices:
        print("❌ Нет голосов! Запустите fetch_eleven_voices.py")
        return
    
    # Запускаем тесты
    tests = [
        ("Получение голосов", tester.test_elevenlabs_voices_direct),
        ("Генерация речи", tester.test_elevenlabs_tts_direct),
        ("Разные голоса", tester.test_multiple_voices),
        ("Производительность", tester.test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"🧪 {test_name}")
        print('='*80)
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: ПРОШЕЛ")
            else:
                print(f"❌ {test_name}: НЕ ПРОШЕЛ")
                
        except Exception as e:
            print(f"❌ {test_name}: ОШИБКА - {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print(f"\n{'='*80}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print('='*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ НЕ ПРОШЕЛ"
        print(f"{test_name}: {status}")
    
    print(f"\n📈 Результат: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли! ElevenLabs работает!")
    elif passed > 0:
        print("⚠️ Частично работает. Проверьте ошибки выше.")
    else:
        print("❌ ElevenLabs не работает.")

if __name__ == "__main__":
    asyncio.run(main())
