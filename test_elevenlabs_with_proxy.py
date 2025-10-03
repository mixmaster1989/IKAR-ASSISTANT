#!/usr/bin/env python3
"""
Тест ElevenLabs TTS через рабочие прокси
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

from backend.utils.proxy_manager import get_proxy_manager

# Загружаем переменные окружения
env_file = PROJECT_ROOT / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Загружен .env файл: {env_file}")
else:
    print(f"⚠️ .env файл не найден: {env_file}")

class ElevenLabsProxyTester:
    """Тестер ElevenLabs через прокси"""
    
    def __init__(self):
        self.proxy_manager = get_proxy_manager()
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
    
    async def test_elevenlabs_voices_with_proxy(self):
        """Тестирует получение голосов ElevenLabs через прокси"""
        print("\n🎤 Тест 1: Получение голосов ElevenLabs через прокси")
        print("=" * 60)
        
        if not self.api_keys:
            print("❌ Нет ключей ElevenLabs!")
            return False
        
        # Получаем лучший HTTP прокси
        proxy = self.proxy_manager.get_best_http_proxy()
        print(f"🌐 Используем прокси: {proxy}")
        
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
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    print(f"📊 Статус: {response.status}")
                    
                    if response.status == 200:
                        voices_data = await response.json()
                        voices = voices_data.get('voices', [])
                        print(f"✅ Получено {len(voices)} голосов через прокси!")
                        
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
    
    async def test_elevenlabs_tts_with_proxy(self):
        """Тестирует генерацию речи ElevenLabs через прокси"""
        print("\n🎤 Тест 2: Генерация речи ElevenLabs через прокси")
        print("=" * 60)
        
        if not self.api_keys or not self.voices:
            print("❌ Нет ключей или голосов!")
            return False
        
        # Выбираем женский голос
        female_voice = next((v for v in self.voices if v.get('gender') == 'female'), self.voices[0])
        print(f"🎤 Используем голос: {female_voice.get('name')} ({female_voice.get('voice_id')})")
        
        # Получаем лучший HTTP прокси
        proxy = self.proxy_manager.get_best_http_proxy()
        print(f"🌐 Используем прокси: {proxy}")
        
        # Тестовый текст
        test_text = "Привет! Это тест ElevenLabs TTS через прокси. Работает отлично!"
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
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    print(f"📊 Статус: {response.status}")
                    
                    if response.status == 200:
                        audio_data = await response.read()
                        print(f"✅ Сгенерировано аудио! Размер: {len(audio_data)} bytes")
                        
                        # Сохраняем аудио
                        os.makedirs("test_audio", exist_ok=True)
                        audio_file = f"test_audio/elevenlabs_proxy_test.mp3"
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
    
    async def test_multiple_proxies(self):
        """Тестирует ElevenLabs через разные прокси"""
        print("\n🎤 Тест 3: ElevenLabs через разные прокси")
        print("=" * 60)
        
        if not self.api_keys or not self.voices:
            print("❌ Нет ключей или голосов!")
            return False
        
        # Тестируем несколько HTTP прокси
        test_proxies = self.proxy_manager.http_proxies[:3]  # Первые 3 прокси
        voice = self.voices[0]
        test_text = "Тест прокси"
        
        results = []
        
        for i, proxy in enumerate(test_proxies):
            print(f"\n🔍 Тестируем прокси {i+1}/3: {proxy}")
            
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
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        if response.status == 200:
                            audio_data = await response.read()
                            print(f"✅ Прокси {proxy} работает! Размер: {len(audio_data)} bytes")
                            results.append((proxy, True, len(audio_data)))
                        else:
                            print(f"❌ Прокси {proxy} не работает: {response.status}")
                            results.append((proxy, False, 0))
                            
            except Exception as e:
                print(f"❌ Прокси {proxy} ошибка: {e}")
                results.append((proxy, False, 0))
        
        # Результаты
        working_proxies = [r for r in results if r[1]]
        print(f"\n📊 Результат: {len(working_proxies)}/{len(test_proxies)} прокси работают")
        
        for proxy, success, size in results:
            status = "✅" if success else "❌"
            print(f"  {status} {proxy} - {size} bytes")
        
        return len(working_proxies) > 0
    
    async def test_proxy_performance(self):
        """Тестирует производительность прокси"""
        print("\n🎤 Тест 4: Производительность прокси")
        print("=" * 60)
        
        if not self.api_keys or not self.voices:
            print("❌ Нет ключей или голосов!")
            return False
        
        import time
        
        # Тестируем лучший прокси
        proxy = self.proxy_manager.get_best_http_proxy()
        voice = self.voices[0]
        test_text = "Тест производительности прокси"
        
        print(f"🌐 Тестируем прокси: {proxy}")
        print(f"🎤 Голос: {voice.get('name')}")
        
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
                    proxy=proxy,
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
    print("🚀 Тестирование ElevenLabs TTS через прокси")
    print("=" * 80)
    
    tester = ElevenLabsProxyTester()
    
    # Тестируем прокси
    print("🔍 Сначала тестируем прокси...")
    working_proxies = await tester.proxy_manager.test_all_proxies()
    
    print(f"📊 Рабочих прокси:")
    print(f"  HTTP: {len(working_proxies['http'])}")
    print(f"  SOCKS4: {len(working_proxies['socks4'])}")
    print(f"  SOCKS5: {len(working_proxies['socks5'])}")
    
    if not working_proxies['http']:
        print("❌ Нет рабочих HTTP прокси!")
        return
    
    # Запускаем тесты
    tests = [
        ("Получение голосов", tester.test_elevenlabs_voices_with_proxy),
        ("Генерация речи", tester.test_elevenlabs_tts_with_proxy),
        ("Множественные прокси", tester.test_multiple_proxies),
        ("Производительность", tester.test_proxy_performance)
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
        print("🎉 Все тесты прошли! ElevenLabs работает через прокси!")
    elif passed > 0:
        print("⚠️ Частично работает. Проверьте ошибки выше.")
    else:
        print("❌ ElevenLabs не работает через прокси.")

if __name__ == "__main__":
    asyncio.run(main())
