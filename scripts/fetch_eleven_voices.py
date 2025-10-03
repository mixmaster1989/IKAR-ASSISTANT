#!/usr/bin/env python3
"""
Робаст-скрипт вытягивает список голосов ElevenLabs и кэширует результат:
- Все голоса → data/eleven_voices.json
- Русские голоса → data/eleven_voices_ru.json

Особенности:
- Ротация ключей: ELEVEN_API / ELEVEN_API_KEY / ELEVEN_API2..ELEVEN_API10
- Поддержка прокси через переменные HTTPS_PROXY/HTTP_PROXY или список ELEVEN_PROXIES (через запятую)
- Заголовки как у обычного клиента (User-Agent/Accept-Language), чтобы снизить шанс 403
- Отчёт об ошибках и сохранение сырых ответов при не-JSON

Запуск:
  set -a; source /home/user1/IKAR/.env; set +a
  /home/user1/IKAR/.venv/bin/python /home/user1/IKAR/scripts/fetch_eleven_voices.py
"""

import os
import json
import sys
from pathlib import Path
import time
from typing import List, Dict
import requests

PROJECT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT / 'data'
DATA_DIR.mkdir(exist_ok=True)
ALL_PATH = DATA_DIR / 'eleven_voices.json'
RU_PATH = DATA_DIR / 'eleven_voices_ru.json'


def collect_keys() -> List[str]:
    keys = []
    base = os.getenv('ELEVEN_API') or os.getenv('ELEVEN_API_KEY')
    if base:
        keys.append(base.strip())
    for i in range(2, 11):
        v = os.getenv(f'ELEVEN_API{i}')
        if v:
            keys.append(v.strip())
    return keys


def parse_proxies() -> List[Dict[str, str]]:
    proxies_env = os.getenv('ELEVEN_PROXIES', '').strip()
    proxies: List[Dict[str, str]] = []
    if proxies_env:
        for p in proxies_env.split(','):
            p = p.strip()
            if p:
                proxies.append({'https': p, 'http': p})
    # Также используем системные
    sys_https = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
    sys_http = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
    if sys_https or sys_http:
        proxies.append({'https': sys_https or '', 'http': sys_http or ''})
    return proxies or [{}]


def fetch_voices(keys: List[str]) -> List[dict]:
    url = 'https://api.elevenlabs.io/v1/voices'
    last_error = None
    headers_common = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'
    }
    session = requests.Session()
    proxies_list = parse_proxies()
    for k in keys:
        headers = dict(headers_common)
        headers['xi-api-key'] = k
        for prx in proxies_list:
            try:
                resp = session.get(url, headers=headers, timeout=25, proxies=prx or None)
                if resp.ok:
                    # Пытаемся распарсить как JSON
                    try:
                        data = resp.json() or {}
                        return data.get('voices') or []
                    except Exception:
                        last_error = f'Non-JSON response ({len(resp.text)} bytes) from {prx}'
                        # Сохраняем сырое тело
                        (DATA_DIR / 'eleven_voices_raw.html').write_text(resp.text, encoding='utf-8')
                else:
                    last_error = f'HTTP {resp.status_code}: {resp.text[:200]}'
                    time.sleep(1)
            except Exception as e:
                last_error = f'{type(e).__name__}: {e}'
                time.sleep(0.5)
    if last_error:
        print(f"[ERR] Не удалось получить список голосов: {last_error}")
    return []


def is_russian_voice(v: dict) -> bool:
    # Eleven может иметь разные поля метаданных. Проверяем name/labels/languages.
    name = (v.get('name') or '').lower()
    labels = v.get('labels') or {}
    lang = (labels.get('language') or labels.get('lang') or '').lower()
    langs = v.get('languages') or []
    if isinstance(langs, list):
        langs = [str(x).lower() for x in langs]
    # эвристики
    if 'ru' in lang or 'russian' in lang:
        return True
    if any(l in ('ru', 'russian', 'ru-ru') for l in langs):
        return True
    if 'russian' in name or 'рус' in name:
        return True
    return False


def main():
    keys = collect_keys()
    if not keys:
        print('[ERR] Ключи ELEVEN_API / ELEVEN_API_KEY не найдены в окружении')
        sys.exit(2)
    voices = fetch_voices(keys)
    # Сохраняем полный список
    with open(ALL_PATH, 'w', encoding='utf-8') as f:
        json.dump(voices, f, ensure_ascii=False, indent=2)
    ru_voices = [v for v in voices if is_russian_voice(v)]
    with open(RU_PATH, 'w', encoding='utf-8') as f:
        json.dump(ru_voices, f, ensure_ascii=False, indent=2)
    print(f"[OK] Сохранено: {ALL_PATH} ({len(voices)}), {RU_PATH} ({len(ru_voices)})")


if __name__ == '__main__':
    main()


