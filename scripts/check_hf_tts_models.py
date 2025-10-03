#!/usr/bin/env python3
"""
Проверка доступности TTS моделей Hugging Face Inference API.

Использование:
  HF_API_TOKEN=... python3 scripts/check_hf_tts_models.py [--synthesize "Привет, проверка!" --save-dir temp/tts_samples]

Поведение:
- Загружает список моделей из scripts/hf_tts_models.json
- Для каждой модели делает HEAD/GET к https://api-inference.huggingface.co/models/{model_id}
- При включённом --synthesize пытается сделать синтез простым JSON {"inputs": "..."}
  и сохранить результат в указанную директорию.

Замечания:
- Некоторые модели требуют дополнительных параметров/форматов. Здесь базовая проверка.
- Для RU лучше всего обычно показывает себя coqui/XTTS-v2.
"""

import os
import json
import argparse
import time
from pathlib import Path
import requests


MODELS_FILE = Path(__file__).parent / 'hf_tts_models.json'
API_MODELS = 'https://api-inference.huggingface.co/models'
API_PIPELINE_TTS = 'https://api-inference.huggingface.co/pipeline/text-to-speech'


def load_models() -> list:
    with open(MODELS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_model_metadata(session: requests.Session, token: str, model_id: str) -> dict:
    # Пытаемся сначала через /models, при 404 пробуем /pipeline/text-to-speech
    url_models = f"{API_MODELS}/{model_id}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = session.get(url_models, headers=headers, timeout=30)
    result = {
        'status_code': resp.status_code,
        'ok': resp.ok,
        'endpoint': 'models',
        'headers': dict(resp.headers),
        'json': safe_json(resp),
        'text': safe_text(resp)
    }
    if resp.status_code == 404:
        url_pipe = f"{API_PIPELINE_TTS}/{model_id}"
        resp2 = session.get(url_pipe, headers=headers, timeout=30)
        result = {
            'status_code': resp2.status_code,
            'ok': resp2.ok,
            'endpoint': 'pipeline/text-to-speech',
            'headers': dict(resp2.headers),
            'json': safe_json(resp2),
            'text': safe_text(resp2)
        }
    return result


def synthesize_sample(session: requests.Session, token: str, model_id: str, text: str, out_dir: Path) -> dict:
    # Пробуем POST на /models, при 404 пробуем /pipeline/text-to-speech
    url_models = f"{API_MODELS}/{model_id}"
    headers = {
        "Authorization": f"Bearer {token}" if token else "",
        "Content-Type": "application/json"
    }
    payload = {"inputs": text}
    start = time.time()
    resp = session.post(url_models, headers=headers, json=payload, timeout=60)
    elapsed = time.time() - start

    result = {
        'status_code': resp.status_code,
        'ok': resp.ok,
        'elapsed_s': round(elapsed, 2),
        'endpoint': 'models',
        'headers': dict(resp.headers)
    }

    if resp.status_code == 404:
        url_pipe = f"{API_PIPELINE_TTS}/{model_id}"
        start = time.time()
        resp = session.post(url_pipe, headers=headers, json=payload, timeout=60)
        elapsed = time.time() - start
        result.update({
            'status_code': resp.status_code,
            'ok': resp.ok,
            'elapsed_s': round(elapsed, 2),
            'endpoint': 'pipeline/text-to-speech',
            'headers': dict(resp.headers)
        })

    if resp.ok and resp.content:
        # Пытаемся сохранить как бинарный аудио-ответ
        ctype = resp.headers.get('content-type', '')
        ext = guess_ext(ctype)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{model_id.replace('/', '_')}{ext}"
        with open(out_path, 'wb') as f:
            f.write(resp.content)
        result['saved'] = str(out_path)
        result['content_type'] = ctype
    else:
        result['json'] = safe_json(resp)
        result['text'] = safe_text(resp)

    return result


def guess_ext(content_type: str) -> str:
    if 'audio/wav' in content_type:
        return '.wav'
    if 'audio/mpeg' in content_type or 'audio/mp3' in content_type:
        return '.mp3'
    if 'audio/ogg' in content_type:
        return '.ogg'
    if 'application/json' in content_type:
        return '.json'
    return '.bin'


def safe_json(resp: requests.Response):
    try:
        return resp.json()
    except Exception:
        return None


def safe_text(resp: requests.Response):
    try:
        return resp.text
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--synthesize', type=str, default=None, help='Текст для тестового синтеза')
    parser.add_argument('--save-dir', type=str, default='temp/tts_samples', help='Куда сохранять аудио')
    args = parser.parse_args()

    token = os.getenv('HF_API_KEY') or os.getenv('HF_API_TOKEN') or ''
    if not token:
        print('⚠️  Не найден HF_API_KEY/HF_API_TOKEN в окружении. Некоторые модели могут возвращать 401/403.')

    models = load_models()
    print(f"🔍 Моделей к проверке: {len(models)}")

    session = requests.Session()
    results = []

    for m in models:
        model_id = m['model_id']
        print(f"\n=== {model_id} ===")
        meta = check_model_metadata(session, token, model_id)
        print(f"META[{meta.get('endpoint')}] : {meta['status_code']} | ok={meta['ok']}")
        if meta.get('json'):
            j = meta['json']
            # Показываем коротко важное
            if isinstance(j, dict):
                err = j.get('error') or j.get('message')
                if err:
                    print(f"  error: {err}")
        elif meta.get('text') and not meta['ok']:
            print(f"  text: {meta['text'][:120]}...")

        syn = None
        if args.synthesize:
            syn = synthesize_sample(session, token, model_id, args.synthesize, Path(args.save_dir))
            print(f"SYN[{syn.get('endpoint')}] : {syn['status_code']} | ok={syn['ok']} | {syn.get('elapsed_s','?')}s | saved={syn.get('saved')}")
            if syn.get('json'):
                j = syn['json']
                if isinstance(j, dict):
                    print(f"  json: {json.dumps(j)[:200]}...")
            elif syn.get('text') and not syn['ok']:
                print(f"  text: {syn['text'][:200]}...")

        results.append({
            'model_id': model_id,
            'meta': meta,
            'synthesis': syn
        })

    # Итоговая сводка
    ok_meta = sum(1 for r in results if r['meta']['ok'])
    ok_syn = sum(1 for r in results if r.get('synthesis') and r['synthesis']['ok'])
    print(f"\n📊 ИТОГО: META ok {ok_meta}/{len(results)} | SYN ok {ok_syn}/{sum(1 for r in results if r.get('synthesis'))}")


if __name__ == '__main__':
    main()


