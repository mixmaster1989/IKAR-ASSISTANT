#!/usr/bin/env python3
"""
Сбор моделей генерации изображений (text-to-image) с Hugging Face.
- Ищет модели по нескольким фильтрам (pipeline_tag, library, ключевые слова)
- Объединяет и дедуплицирует результаты
- Сохраняет в reports/hf_text2img_models.jsonl и .csv

Запуск:
  python3 scripts/collect_hf_text2img_models.py --limit 1500

Примечание: Скрипт только собирает метаданные, ничего не скачивает.
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Загрузка .env (НЕ меняем .env и не требуем его наличия)
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

try:
	from huggingface_hub import HfApi
	# В новых версиях ModelFilter заменен на параметры в list_models
except Exception as e:
	print("❌ Не удалось импортировать huggingface_hub. Добавьте 'huggingface_hub' в requirements.txt")
	raise

OUTPUT_DIR = Path(__file__).resolve().parents[1] / 'reports'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
JSONL_PATH = OUTPUT_DIR / 'hf_text2img_models.jsonl'
CSV_PATH = OUTPUT_DIR / 'hf_text2img_models.csv'

KEYWORD_QUERIES = [
	"text-to-image",
	"stable-diffusion",
	"sdxl",
	"sd 1.5",
	"kandinsky",
	"anything v4",
	"realistic vision",
	"flux",
	"animated",
	"cartoon",
]


def model_to_row(m) -> dict:
	"""Безопасное извлечение основных полей из ModelInfo."""
	return {
		'modelId': getattr(m, 'modelId', getattr(m, 'id', '')),
		'pipeline_tag': getattr(m, 'pipeline_tag', ''),
		'library': getattr(m, 'library_name', ''),
		'likes': getattr(m, 'likes', 0) or 0,
		'downloads': getattr(m, 'downloads', 0) or 0,
		'private': bool(getattr(m, 'private', False)),
		'gated': bool(getattr(m, 'gated', False)),
		'lastModified': str(getattr(m, 'lastModified', '')),
	}


def save_results(models: list):
	# Сохраняем JSONL
	with open(JSONL_PATH, 'w', encoding='utf-8') as jf:
		for row in models:
			jf.write(json.dumps(row, ensure_ascii=False) + "\n")
	# Сохраняем CSV
	fieldnames = list(models[0].keys()) if models else [
		'modelId','pipeline_tag','library','likes','downloads','private','gated','lastModified']
	with open(CSV_PATH, 'w', newline='', encoding='utf-8') as cf:
		writer = csv.DictWriter(cf, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(models)
	print(f"✅ Сохранено: {len(models)} моделей -> {JSONL_PATH} и {CSV_PATH}")


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--limit', type=int, default=1500, help='Максимум моделей на фильтр')
	args = parser.parse_args()

	api = HfApi()
	all_rows = {}

	# 1) Базовый фильтр: diffusers + pipeline_tag text-to-image
	try:
		models = api.list_models(
			library="diffusers",
			pipeline_tag="text-to-image",
			limit=args.limit,
			sort='downloads'
		)
		for m in models:
			row = model_to_row(m)
			if row['modelId']:
				all_rows[row['modelId']] = row
		count = 0
		for m in models:
			row = model_to_row(m)
			if row['modelId']:
				all_rows[row['modelId']] = row
				count += 1
		print(f"🔎 Найдено (diffusers + text-to-image): {count}")
	except Exception as e:
		print(f"⚠️ Ошибка при запросе diffusers/text-to-image: {e}")

	# 2) Только pipeline_tag text-to-image (любая библиотека)
	try:
		models = api.list_models(
			pipeline_tag="text-to-image",
			limit=args.limit,
			sort='downloads'
		)
		count = 0
		for m in models:
			row = model_to_row(m)
			if row['modelId']:
				all_rows[row['modelId']] = row
				count += 1
		print(f"🔎 Найдено (pipeline_tag=text-to-image): {count}")
	except Exception as e:
		print(f"⚠️ Ошибка при запросе pipeline_tag=text-to-image: {e}")

	# 3) По ключевым словам (добавочные охваты)
	for q in KEYWORD_QUERIES:
		try:
			models = api.list_models(search=q, limit=args.limit, sort='downloads')
			count = 0
			for m in models:
				row = model_to_row(m)
				if row['modelId']:
					all_rows[row['modelId']] = row
					count += 1
			print(f"🔎 Найдено ('{q}'): {count}")
		except Exception as e:
			print(f"⚠️ Ошибка при поиске '{q}': {e}")

	# Дедупликация и сортировка
	rows = list(all_rows.values())
	rows.sort(key=lambda r: (-int(r.get('downloads', 0) or 0), -int(r.get('likes', 0) or 0)))

	save_results(rows)


if __name__ == '__main__':
	main()
