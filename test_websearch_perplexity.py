#!/usr/bin/env python3
"""
Тест веб-поиска у модели perplexity/sonar через OpenRouter с платным ключом.

Версия на requests. Ключи читаются из .env через python-dotenv (не редактируем .env вручную).
Проверяем: текущая дата, погода сейчас, новости вчера. Эвристика: наличие URL в ответе.
"""

import os
import re
import json
import datetime as dt
import requests

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

def load_env_if_possible():
    if load_dotenv is not None:
        root = os.path.dirname(os.path.abspath(__file__))
        dot_env = os.path.join(root, ".env")
        if os.path.exists(dot_env):
            load_dotenv(dot_env)

def get_headers():
    api_key = os.getenv("OPENROUTER_API_KEY_PAID") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Нет OPENROUTER_API_KEY_PAID/OPENROUTER_API_KEY в окружении/.env")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ikar.local",
        "X-Title": "IKAR Assistant",
    }

def chat(messages, model="perplexity/sonar", temperature=0.0):
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    r = requests.post(url, headers=get_headers(), data=json.dumps(payload), timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

def has_urls(text: str) -> bool:
    return bool(re.search(r"https?://", text or ""))

def test_image_caption():
    msgs = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "What is in this image?"},
            {"type": "image_url", "image_url": {
                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
            }},
        ],
    }]
    txt = chat(msgs)
    print("\n=== IMAGE CAPTION ===")
    print(txt)

def test_web_checks():
    today = dt.datetime.now().strftime("%Y-%m-%d")
    tests = [
        ("date", "Скажи текущую дату в формате YYYY-MM-DD. Укажи источники со ссылками."),
        ("weather_now", "Какая сейчас погода в Москве? Приведи источники со ссылками и время обновления."),
        ("news_yesterday", "Топ-3 новости России за вчера. Дай краткие сводки и источники со ссылками."),
    ]
    any_web = False
    for tag, prompt in tests:
        msgs = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        txt = chat(msgs)
        print(f"\n=== TEST: {tag} ===")
        print(txt)
        url_flag = has_urls(txt)
        any_web = any_web or url_flag
        print(f"\n[web_search_detected={url_flag}]")
    # грубая проверка даты
    msgs = [{"role": "user", "content": [{"type": "text", "text": "Скажи текущую дату в формате YYYY-MM-DD без пояснений."}]}]
    txt = chat(msgs)
    print(f"\nГРУБАЯ ПРОВЕРКА ДАТЫ: ожидаемо≈{today}, ответ={txt.strip()}")
    print(f"\nИТОГ: веб-поиск {'обнаружен' if any_web else 'не обнаружен (по эвристике ссылок)'}")

if __name__ == "__main__":
    load_env_if_possible()
    test_image_caption()
    test_web_checks()


