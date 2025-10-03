#!/usr/bin/env python3
"""
Скрипт для поиска и тестирования бесплатных прокси
"""

import requests
import time
import random

def get_proxies_from_api():
    """Получает прокси из публичных API"""
    print("🔍 Получение прокси из API...")
    
    proxies = []
    
    try:
        # API 1: proxylist.geonode.com
        url = "https://proxylist.geonode.com/api/proxy-list?limit=10&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps&anonymityLevel=elite&country=US"
        resp = requests.get(url, timeout=10)
        if resp.ok:
            data = resp.json()
            for proxy in data.get('data', []):
                ip = proxy.get('ip')
                port = proxy.get('port')
                if ip and port:
                    proxies.append(f"{ip}:{port}")
            print(f"✅ Получено {len(proxies)} прокси из geonode")
    except:
        pass
    
    try:
        # API 2: proxyscrape.com
        url = "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        resp = requests.get(url, timeout=10)
        if resp.ok:
            lines = resp.text.strip().split('\n')
            for line in lines:
                if ':' in line and line.strip():
                    proxies.append(line.strip())
            print(f"✅ Получено {len(lines)} прокси из proxyscrape")
    except:
        pass
    
    return list(set(proxies))  # Убираем дубликаты

def test_proxy(proxy):
    """Тестирует прокси"""
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        # Тест 1: httpbin.org
        resp = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
        if resp.ok:
            print(f"✅ {proxy} - работает")
            return True
            
    except Exception as e:
        pass
    
    return False

def find_free_proxies():
    """Ищет бесплатные прокси"""
    print("🔍 Поиск бесплатных прокси...")
    
    # Получаем прокси из API
    proxy_list = get_proxies_from_api()
    
    # Добавляем статичные прокси
    static_proxies = [
        "103.149.162.194:80",
        "103.149.162.195:80", 
        "103.149.162.196:80",
        "103.149.162.197:80",
        "103.149.162.198:80",
        "103.149.162.199:80",
        "103.149.162.200:80",
        "103.149.162.201:80",
        "103.149.162.202:80",
        "103.149.162.203:80",
        "103.149.162.204:80",
        "103.149.162.205:80",
        "103.149.162.206:80",
        "103.149.162.207:80",
        "103.149.162.208:80",
        "103.149.162.209:80",
        "103.149.162.210:80",
        "103.149.162.211:80",
        "103.149.162.212:80",
        "103.149.162.213:80"
    ]
    
    proxy_list.extend(static_proxies)
    proxy_list = list(set(proxy_list))  # Убираем дубликаты
    
    print(f"🔍 Всего прокси для тестирования: {len(proxy_list)}")
    
    working_proxies = []
    
    for i, proxy in enumerate(proxy_list[:20]):  # Тестируем первые 20
        print(f"🔍 Тестируем {i+1}/{min(20, len(proxy_list))}: {proxy}...")
        if test_proxy(proxy):
            working_proxies.append(proxy)
            print(f"✅ Найден рабочий прокси: {proxy}")
            break  # Останавливаемся на первом рабочем
        time.sleep(1)
    
    return working_proxies

def test_elevenlabs_with_proxy(proxy):
    """Тестирует ElevenLabs с прокси"""
    print(f"🎤 Тестируем ElevenLabs с прокси {proxy}...")
    
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        # Тест ElevenLabs API
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": "sk_0da4451bbc1b4513626d8dabfaa3dd75e4672d478e23ffbc"}
        
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15, verify=False)
        
        if resp.ok:
            print(f"🎉 ElevenLabs работает с прокси {proxy}!")
            return True
        else:
            print(f"❌ ElevenLabs не работает с прокси {proxy}: {resp.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка с прокси {proxy}: {e}")
    
    return False

if __name__ == '__main__':
    print("🚀 Поиск прокси для ElevenLabs...")
    
    # Ищем прокси
    working_proxies = find_free_proxies()
    
    if working_proxies:
        print(f"\n✅ Найдено {len(working_proxies)} рабочих прокси:")
        for proxy in working_proxies:
            print(f"  - {proxy}")
        
        # Тестируем с ElevenLabs
        for proxy in working_proxies:
            if test_elevenlabs_with_proxy(proxy):
                print(f"\n🎉 УСПЕХ! Используй прокси: {proxy}")
                print(f"Добавь в .env: ELEVEN_PROXIES=http://{proxy}")
                break
    else:
        print("❌ Рабочие прокси не найдены")
