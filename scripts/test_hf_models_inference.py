#!/usr/bin/env python3
"""
Асинхронный тестер Hugging Face Inference API для моделей text-to-image.
- Читает список моделей из reports/hf_text2img_models.jsonl (если нет — предложит сначала собрать)
- Шлет короткий промпт на /models/{model_id}
- Фиксирует успех (image/*) или ошибку (JSON)
- Пишет логи и результаты в reports/hf_inference_test_results.jsonl

ВНИМАНИЕ: НИЧЕГО НЕ ЗАПУСКАЕТСЯ АВТОМАТИЧЕСКИ БЕЗ РАЗРЕШЕНИЯ.
Запуск (после подтверждения):
  python3 scripts/test_hf_models_inference.py --max 400 --concurrency 3 --timeout 45
"""

import os
import sys
import json
import time
import argparse
import signal
from pathlib import Path
from typing import Optional, Tuple
import asyncio
from datetime import datetime

from dotenv import load_dotenv
import aiohttp

# Загрузка .env
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

HF_TOKEN = os.environ.get('HF_API_KEY') or os.environ.get('HF_API_TOKEN') or os.environ.get('HUGGINGFACEHUB_API_TOKEN') or ''
API_URL_BASE = 'https://api-inference.huggingface.co/models/'

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
REPORTS.mkdir(parents=True, exist_ok=True)
MODELS_JSONL = REPORTS / 'hf_text2img_models.jsonl'
RESULTS_JSONL = REPORTS / 'hf_inference_test_results.jsonl'

TEST_PROMPT = (
	"A realistic red cat on a windowsill, sunlight, cozy atmosphere, photorealistic, 4k, high detail"
)

HEADERS = {
	"Accept": "image/png,image/jpeg,image/jpg,image/webp,application/json",
}
if HF_TOKEN:
	HEADERS["Authorization"] = f"Bearer {HF_TOKEN}"


def load_models(max_models: int) -> list:
	"""Загружает список моделей из JSONL, ограничивает max_models."""
	if not MODELS_JSONL.exists():
		raise FileNotFoundError(
			f"Не найден {MODELS_JSONL}. Сначала соберите модели: python3 scripts/collect_hf_text2img_models.py"
		)
	models = []
	with open(MODELS_JSONL, 'r', encoding='utf-8') as f:
		for line in f:
			try:
				obj = json.loads(line)
				mid = obj.get('modelId') or obj.get('id')
				if not mid:
					continue
				# Предпочитаем явные text-to-image
				ptag = (obj.get('pipeline_tag') or '').lower()
				if 'text-to-image' in ptag or 'text2image' in ptag or 'text2img' in ptag:
					models.append(mid)
				else:
					# Дополнительный охват diffusers/stable-diffusion
					lib = (obj.get('library') or '').lower()
					name = mid.lower()
					if 'diffusers' in lib or 'stable-diffusion' in name or 'sdxl' in name or 'flux' in name:
						models.append(mid)
			except:
				continue
	# Дедуп и усечение
	seen = set()
	uniq = []
	for m in models:
		if m not in seen:
			uniq.append(m)
			seen.add(m)
	return uniq[:max_models]


async def test_model(session: aiohttp.ClientSession, model_id: str, timeout: int) -> Tuple[str, str, Optional[str], int]:
	"""Возвращает (model_id, status, error, elapsed_ms). Успех, если image/*."""
	url = API_URL_BASE + model_id
	payload = {"inputs": TEST_PROMPT}
	start = time.time()
	try:
		async with session.post(url, json=payload, timeout=timeout) as resp:
			ct = resp.headers.get('content-type', '')
			data = await resp.read()
			elapsed = int((time.time() - start) * 1000)
			if resp.status == 200 and ct.startswith('image/'):
				return (model_id, 'success', None, elapsed)
			# Иначе пытаемся распарсить ошибку
			try:
				err = json.loads(data.decode('utf-8'))
				err_msg = err.get('error') or err.get('message') or str(err)
			except Exception:
				err_msg = f"HTTP {resp.status}, content-type={ct}"
			return (model_id, 'error', err_msg, elapsed)
	except asyncio.TimeoutError:
		elapsed = int((time.time() - start) * 1000)
		return (model_id, 'timeout', 'request timed out', elapsed)
	except Exception as e:
		elapsed = int((time.time() - start) * 1000)
		return (model_id, 'exception', str(e), elapsed)


# Глобальные переменные для обработки сигналов
shutdown_requested = False
completed_count = 0

def signal_handler(signum, frame):
	global shutdown_requested
	print(f"\n⚠️ Получен сигнал {signum}, завершаем работу...")
	shutdown_requested = True

async def run(max_models: int, concurrency: int, timeout: int, resume: bool):
	global completed_count
	
	# Регистрируем обработчики сигналов
	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)
	
	models = load_models(max_models)
	print(f"🔢 К тестированию: {len(models)} моделей")

	# Резюмирование по уже протестированным моделям
	already = set()
	if resume and RESULTS_JSONL.exists():
		with open(RESULTS_JSONL, 'r', encoding='utf-8') as rf:
			for line in rf:
				try:
					obj = json.loads(line)
					already.add(obj.get('model_id'))
				except:
					continue
	if already:
		models = [m for m in models if m not in already]
		print(f"⏩ Пропущено уже протестированных: {len(already)} | Осталось: {len(models)}")
	
	# Создаем файл с метаинформацией о тесте
	meta_path = REPORTS / 'hf_inference_test_meta.json'
	meta = {
		'started_at': datetime.now().isoformat(),
		'total_models': len(models),
		'already_tested': len(already),
		'concurrency': concurrency,
		'timeout': timeout,
		'test_prompt': TEST_PROMPT
	}
	with open(meta_path, 'w', encoding='utf-8') as mf:
		json.dump(meta, mf, ensure_ascii=False, indent=2)
	print(f"📋 Метаинформация сохранена в: {meta_path}")

	sem = asyncio.Semaphore(concurrency)

	async def bound_test(mid: str):
		async with sem:
			async with aiohttp.ClientSession(headers=HEADERS) as session:
				res = await test_model(session, mid, timeout)
				# Сохраняем сразу, чтобы резюмировать при прерывании
				record = {
					'model_id': res[0],
					'status': res[1],
					'error': res[2],
					'elapsed_ms': res[3],
					'tested_at': datetime.now().isoformat()
				}
				with open(RESULTS_JSONL, 'a', encoding='utf-8') as wf:
					wf.write(json.dumps(record, ensure_ascii=False) + "\n")
				print(f"[{res[1]:>9}] {mid} | {res[3]} ms | {res[2] or ''}")

	# Итеративно, чтобы контролировать нагрузку
	start_time = time.time()
	completed = 0
	
	print(f"\n🚀 Начинаем тестирование {len(models)} моделей...")
	print(f"📊 Параллельность: {concurrency}, таймаут: {timeout}с")
	print("💡 Прервать можно в любой момент (Ctrl+C) - результаты сохранятся\n")
	
	try:
		for i, mid in enumerate(models, 1):
			if shutdown_requested:
				print(f"\n⚠️ Завершение по сигналу на модели {i-1}/{len(models)}")
				break
				
			await bound_test(mid)
			completed_count = i
			
			# Показываем прогресс каждые 10 моделей
			if i % 10 == 0:
				elapsed = time.time() - start_time
				rate = i / elapsed if elapsed > 0 else 0
				eta = (len(models) - i) / rate if rate > 0 else 0
				print(f"📈 Прогресс: {i}/{len(models)} ({i/len(models)*100:.1f}%) | Скорость: {rate:.1f} мод/с | Осталось: {eta/60:.1f} мин")
				
	except KeyboardInterrupt:
		print(f"\n⚠️ Тестирование прервано пользователем на модели {completed_count}/{len(models)}")
		print("💾 Все промежуточные результаты сохранены!")
	except Exception as e:
		print(f"\n❌ Ошибка тестирования: {e}")
		print("💾 Все промежуточные результаты сохранены!")
	
	# Финальная статистика
	total_time = time.time() - start_time
	success_count = 0
	error_count = 0
	timeout_count = 0
	
	if RESULTS_JSONL.exists():
		with open(RESULTS_JSONL, 'r', encoding='utf-8') as rf:
			for line in rf:
				try:
					obj = json.loads(line)
					status = obj.get('status', '')
					if status == 'success':
						success_count += 1
					elif status == 'error':
						error_count += 1
					elif status == 'timeout':
						timeout_count += 1
				except:
					continue
	
	print(f"\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
	print(f"   ✅ Успешно: {success_count}")
	print(f"   ❌ Ошибки: {error_count}")
	print(f"   ⏰ Таймауты: {timeout_count}")
	print(f"   ⏱️  Общее время: {total_time/60:.1f} мин")
	print(f"   📁 Результаты: {RESULTS_JSONL}")
	print(f"   📋 Метаинформация: {REPORTS}/hf_inference_test_meta.json")
	print("\n💡 Для продолжения используйте: --resume")


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--max', type=int, default=400, help='Макс. число моделей для теста')
	parser.add_argument('--concurrency', type=int, default=3, help='Параллельность запросов')
	parser.add_argument('--timeout', type=int, default=45, help='Таймаут запроса, сек')
	parser.add_argument('--resume', action='store_true', help='Продолжить с места остановки (не тестировать уже записанные)')
	args = parser.parse_args()

	if not MODELS_JSONL.exists():
		print(f"❌ Не найден список моделей: {MODELS_JSONL}")
		print("   Сначала выполните сбор: python3 scripts/collect_hf_text2img_models.py")
		return 2

	if not HF_TOKEN:
		print("⚠️ Переменная HF_API_KEY не установлена. Попытаемся без токена (многие модели могут не работать)")

	asyncio.run(run(args.max, args.concurrency, args.timeout, args.resume))
	return 0


if __name__ == '__main__':
	sys.exit(main())
