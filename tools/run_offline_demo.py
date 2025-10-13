#!/usr/bin/env python3
import os, json, re, sys, datetime
from pathlib import Path
import requests

def load_env():
    try:
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parents[1]
        envp = root / '.env'
        if envp.exists():
            load_dotenv(str(envp))
    except Exception:
        pass

def sonar_facts(prompt: str) -> str:
    api_key = os.getenv('OPENROUTER_API_KEY_PAID') or os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise RuntimeError('Нет OPENROUTER_API_KEY_PAID/OPENROUTER_API_KEY')
    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://ikar.local',
        'X-Title': 'IKAR Assistant',
    }
    # Просим краткую сводку без ссылок, с датами/цифрами
    user_text = (
        'Сделай очень короткую факт-сводку по пунктам (без ссылок!), '
        'укажи даты/цифры/имена, только проверяемые факты по запросу: '\
        + prompt
    )
    body = {
        'model': 'perplexity/sonar',
        'messages': [{
            'role': 'user',
            'content': [{ 'type': 'text', 'text': user_text }]
        }],
        'temperature': 0.0,
        'metadata': {'cache': True}
    }
    r = requests.post(url, headers=headers, data=json.dumps(body), timeout=120)
    r.raise_for_status()
    data = r.json()
    return (data['choices'][0]['message']['content'] or '').strip()

def grok_reply(system_prompt: str, user_prompt: str) -> str:
    api_key = os.getenv('OPENROUTER_API_KEY_PAID') or os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise RuntimeError('Нет OPENROUTER_API_KEY_PAID/OPENROUTER_API_KEY')
    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://ikar.local',
        'X-Title': 'IKAR Assistant',
    }
    body = {
        'model': 'x-ai/grok-4-fast',
        'messages': [
            { 'role': 'system', 'content': system_prompt },
            { 'role': 'user', 'content': user_prompt },
        ],
        'temperature': 0.4,
    }
    r = requests.post(url, headers=headers, data=json.dumps(body), timeout=180)
    r.raise_for_status()
    data = r.json()
    return (data['choices'][0]['message']['content'] or '').strip()

def main():
    load_env()
    # Тестовый запрос: комбинирует интернет и экспертность ИКАР
    prompt = (
        'Дай 2–3 свежих факта за вчера по 1С/ККТ (без ссылок), '
        'а затем порекомендуй для магазина одежды Эвотор 10 или Sigma 7 '
        'с коротким расчётом "под ключ".'
    )
    facts = sonar_facts(prompt)
    # Системный стиль (краткий вариант Икар Икарыча)
    system = (
        'Ты Икар Икарыч — опытный сотрудник «ИКАР», профессиональный и краткий. '
        'Используй блок Актуально из интернета как источник свежих фактов.'
    )
    user = (
        'Актуально из интернета (факты, без ссылок):\n'
        + facts + '\n\n'
        'Задача: ' + prompt + '\n'
        'Ответ будь кратким и по делу; если надо — сделай таблицу цен.'
    )
    answer = grok_reply(system, user)

    out_dir = Path(__file__).resolve().parents[1] / 'reports'
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = out_dir / f'DEMO_WEBSEARCH_{ts}.md'
    md = (
        f'# DEMO WEBSEARCH {ts}\n\n'
        f'## Запрос\n\n{prompt}\n\n'
        '## Актуально из интернета (факты)\n\n'
        f'{facts}\n\n'
        '## Ответ ассистента\n\n'
        f'{answer}\n'
    )
    out_path.write_text(md, encoding='utf-8')
    print(str(out_path))

if __name__ == '__main__':
    main()


