#!/usr/bin/env python3
"""
Тест ElevenLabs TTS с обходом Cloudflare через прокси
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

class ElevenLabsCloudflareBypass:
    """Тестер ElevenLabs с обходом Cloudflare"""
    
    def __init__(self):
        self.api_keys = self._collect_api_keys()
        self.voices = self._load_voices()
        
        # Прокси для обхода Cloudflare
        self.proxies = [
            "http://43.156.66.39:8080",      # Сингапур
            "http://65.21.34.102:80",        # Финляндия
            "http://103.156.75.213:8787",    # Индонезия
            "http://109.135.16.145:8789",    # Бельгия
            "http://47.89.184.18:3128",      # США
        ]
        
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
    
    async def test_proxy_with_cloudflare_bypass(self, proxy: str) -> bool:
        """Тестирует прокси с обходом Cloudflare"""
        print(f"\n🔍 Тестируем прокси: {proxy}")
        
        # Заголовки для обхода Cloudflare
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
        
        try:
            async with aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                # Сначала тестируем простой запрос
                async with session.get(
                    "http://httpbin.org/ip",
                    proxy=proxy
                ) as response:
                    if response.status == 200:
                        ip_data = await response.json()
                        print(f"✅ Прокси работает! IP: {ip_data.get('origin')}")
                        
                        # Теперь тестируем ElevenLabs
                        return await self._test_elevenlabs_with_proxy(session, proxy)
                    else:
                        print(f"❌ Прокси не работает: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Ошибка прокси: {e}")
            return False
    
    async def _test_elevenlabs_with_proxy(self, session: aiohttp.ClientSession, proxy: str) -> bool:
        """Тестирует ElevenLabs через прокси"""
        
        if not self.api_keys or not self.voices:
            return False
        
        # Заголовки для ElevenLabs
        eleven_headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_keys[0],
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site"
        }
        
        try:
            # Тестируем получение голосов
            async with session.get(
                "https://api.elevenlabs.io/v1/voices",
                headers=eleven_headers,
                proxy=proxy
            ) as response:
                
                print(f"📊 ElevenLabs API статус: {response.status}")
                
                if response.status == 200:
                    voices_data = await response.json()
                    voices = voices_data.get('voices', [])
                    print(f"✅ Получено {len(voices)} голосов через прокси!")
                    return True
                elif response.status == 403:
                    print("❌ Cloudflare блокирует запрос (403)")
                    return False
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка API: {response.status}")
                    print(f"📄 Ответ: {error_text[:200]}...")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка ElevenLabs: {e}")
            return False
    
    async def test_elevenlabs_tts_with_cloudflare_bypass(self):
        """Тестирует генерацию речи с обходом Cloudflare через прокси с ретраями"""
        print("\n🎤 Тест: Генерация речи ElevenLabs с обходом Cloudflare")
        print("=" * 60)
        
        if not self.api_keys or not self.voices:
            print("❌ Нет ключей или голосов!")
            return False
        
        # Выбираем голос
        voice = self.voices[0]
        print(f"🎤 Используем голос: {voice.get('name')} ({voice.get('voice_id')})")
        
        # Тестовый текст
        test_text = "Привет! Это тест ElevenLabs TTS с обходом Cloudflare!"
        print(f"📝 Текст: {test_text}")
        
        # Пробуем разные прокси с ретраями
        for i, proxy in enumerate(self.proxies):
            print(f"\n🔍 Пробуем прокси {i+1}/{len(self.proxies)}: {proxy}")
            
            # Ретраи для каждого прокси
            for retry in range(3):
                print(f"  🔄 Попытка {retry + 1}/3...")
                
                try:
                    # Заголовки для обхода Cloudflare
                    headers = {
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": self.api_keys[0],
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Sec-Fetch-Dest": "empty",
                        "Sec-Fetch-Mode": "cors",
                        "Sec-Fetch-Site": "cross-site"
                    }
                    
                    data = {
                        "text": test_text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.5
                        }
                    }
                    
                    async with aiohttp.ClientSession(
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as session:
                        async with session.post(
                            f"https://api.elevenlabs.io/v1/text-to-speech/{voice.get('voice_id')}",
                            headers=headers,
                            json=data,
                            proxy=proxy
                        ) as response:
                            
                            print(f"  📊 Статус: {response.status}")
                            
                            if response.status == 200:
                                audio_data = await response.read()
                                print(f"✅ Сгенерировано аудио! Размер: {len(audio_data)} bytes")
                                
                                # Сохраняем аудио
                                os.makedirs("test_audio", exist_ok=True)
                                audio_file = f"test_audio/elevenlabs_proxy_{i+1}_retry_{retry+1}.mp3"
                                with open(audio_file, "wb") as f:
                                    f.write(audio_data)
                                print(f"💾 Аудио сохранено: {audio_file}")
                                
                                return True
                            elif response.status == 403:
                                print("  ❌ Cloudflare блокирует запрос (403)")
                                if retry < 2:
                                    print("  ⏳ Ждем 2 секунды перед повтором...")
                                    await asyncio.sleep(2)
                            else:
                                error_text = await response.text()
                                print(f"  ❌ Ошибка API: {response.status}")
                                print(f"  📄 Ответ: {error_text[:100]}...")
                                if retry < 2:
                                    print("  ⏳ Ждем 2 секунды перед повтором...")
                                    await asyncio.sleep(2)
                                
                except Exception as e:
                    print(f"  ❌ Ошибка: {e}")
                    if retry < 2:
                        print("  ⏳ Ждем 2 секунды перед повтором...")
                        await asyncio.sleep(2)
        
        print("❌ Все прокси не смогли обойти Cloudflare")
        return False
    
    async def test_all_proxies_cloudflare_bypass(self):
        """Тестирует все прокси на обход Cloudflare с ретраями"""
        print("\n🔍 Тест: Обход Cloudflare через все прокси с ретраями")
        print("=" * 60)
        
        working_proxies = []
        
        for i, proxy in enumerate(self.proxies):
            print(f"\n🔍 Тестируем прокси {i+1}/{len(self.proxies)}: {proxy}")
            
            # Ретраи для каждого прокси
            success = False
            for retry in range(3):
                print(f"  🔄 Попытка {retry + 1}/3...")
                
                if await self.test_proxy_with_cloudflare_bypass(proxy):
                    working_proxies.append(proxy)
                    print(f"✅ Прокси {proxy} работает с ElevenLabs!")
                    success = True
                    break
                else:
                    print(f"  ❌ Прокси {proxy} не работает с ElevenLabs (попытка {retry + 1})")
                    if retry < 2:
                        print("  ⏳ Ждем 2 секунды перед повтором...")
                        await asyncio.sleep(2)
            
            if not success:
                print(f"❌ Прокси {proxy} не работает с ElevenLabs после всех попыток")
        
        print(f"\n📊 Результат: {len(working_proxies)}/{len(self.proxies)} прокси работают с ElevenLabs")
        
        for proxy in working_proxies:
            print(f"  ✅ {proxy}")
        
        return len(working_proxies) > 0

async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование ElevenLabs TTS с обходом Cloudflare")
    print("=" * 80)
    
    tester = ElevenLabsCloudflareBypass()
    
    if not tester.api_keys:
        print("❌ Нет ключей ElevenLabs! Проверьте .env файл.")
        return
    
    if not tester.voices:
        print("❌ Нет голосов! Запустите fetch_eleven_voices.py")
        return
    
    # Запускаем тесты
    tests = [
        ("Обход Cloudflare через все прокси", tester.test_all_proxies_cloudflare_bypass),
        ("Генерация речи с обходом Cloudflare", tester.test_elevenlabs_tts_with_cloudflare_bypass)
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
        print("🎉 Все тесты прошли! ElevenLabs работает с обходом Cloudflare!")
    elif passed > 0:
        print("⚠️ Частично работает. Проверьте ошибки выше.")
    else:
        print("❌ ElevenLabs не работает даже с обходом Cloudflare.")

if __name__ == "__main__":
    asyncio.run(main())
