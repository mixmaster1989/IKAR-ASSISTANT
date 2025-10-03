# TODO: Рефакторинг IKAR / «Чатумба»

Цель: укрепить стабильность, безопасность, читаемость и DX, сохранив живую «личность» проекта.

## Готово (сделано)
- [x] Синхронизирован порт 6666 во фронте и старт-скриптах
  - frontend/public/app.js, frontend/public/soul.html, test/start.ps1, test/start.bat, start.sh, run.py, test/debug_prompts.sh
- [x] Подключён admin_router к FastAPI (маршруты доступны по `/api/admin/*`)
  - backend/main.py
- [x] Минимальная защита админки токеном (включается при наличии `ADMIN_API_TOKEN`)
  - backend/api/admin_api.py
- [x] Убран лишний ре-импорт `get_lazy_memory` внутри обработчика
  - backend/api/routes.py
- [x] Добавлен шаблон переменных окружения
  - .env.example

## Итерация 1 — Конфигурация и безопасность
- [ ] Перенести конфигурацию на Pydantic Settings (валидация env, типобезопасность)
- [ ] Убрать дефолтные секреты (например, HF_API_KEY) — только через env, с явной проверкой на старте
- [ ] Консолидировать Admin API (устранить дубли из telegram_core/admin_api; единая зависимость `require_admin`)
- [ ] Перевести «горячие» SQL-операции админки на `aiosqlite` или `run_in_executor`
- [ ] Сузить CORS (белый список доменов из ENV)

## Итерация 2 — Структура и async
- [ ] Убрать `sys.path.append` и оформить проект как пакет; перейти на относительные импорты
- [ ] Ввести слой репозиториев (SQLite) и сервисов; роуты — тонкие
- [ ] Очередь/пул для тяжёлых задач (TTS, OCR, генерация изображений)
- [ ] Ленивая инициализация TTS/Vision и кэш артефактов

## Итерация 3 — Наблюдаемость и устойчивость
- [ ] Структурные логи (JSON) + middleware для request/correlation ID
- [ ] Метрики: LLM (успех/ошибки/ретраи/латентность), ретривер/FAISS, фоновые очереди
- [ ] Расширенный `/health`: состояние памяти, оптимизатора, очередей

## LLM / Промпты / Память
- [ ] Централизовать per-model лимиты: `max_tokens`, `timeout`, `retries`
- [ ] Вынести шаблоны промптов и покрыть unit-тестами `prompt_builder`
- [ ] Ввести интерфейсы `MemoryStore`/`Retriever`, описать конкуренцию доступа

## DX / Деплой / Документация
- [ ] Dockerfile + docker-compose (профили CPU/GPU)
- [ ] README: Quick Start, пример `.env`, команды healthcheck; ссылки на порт 6666
- [ ] Обновить docs/*: единый порт 6666 в примерах
- [ ] Контрактные API-тесты (FastAPI TestClient)
- [ ] Pre-commit (ruff/black/isort; опционально mypy)

## Примечания
- Для защиты админки установите `ADMIN_API_TOKEN` в `.env` и передавайте токен:
  - `Authorization: Bearer <TOKEN>` или заголовок `X-Admin-Token: <TOKEN>` или `?token=<TOKEN>`

