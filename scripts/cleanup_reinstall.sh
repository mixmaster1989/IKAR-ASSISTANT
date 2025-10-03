#!/usr/bin/env bash

# Скрипт очистки проекта IKAR и переустановки окружения (CPU-only)
# НИЧЕГО НЕ ЗАПУСКАЕТ САМ ПО СЕБЕ, ЗАПУСК ТОЛЬКО ПОД ВАШ КОНТРОЛЬ
# Использует абсолютные пути и аккуратно чистит всё лишнее.
#
# Переменные-опции (задайте перед запуском при необходимости):
#   STOP_PM2=1              — остановить PM2-процессы туннелей перед чисткой
#   HANDLE_MODELS=archive   — как обрабатывать модели .pt (archive|delete|keep), по умолчанию: archive
#   COMPRESS_BACKUPS=1      — сжать папку backups и удалить оригинал
#   PURGE_EXPORTED=1        — удалить содержимое exported_memory (ОСТОРОЖНО)
#   PURGE_DATA=1            — удалить содержимое data (ОСТОРОЖНО)
#
# Пример запуска:
#   chmod +x /home/user1/IKAR/scripts/cleanup_reinstall.sh
#   STOP_PM2=1 HANDLE_MODELS=archive COMPRESS_BACKUPS=1 /home/user1/IKAR/scripts/cleanup_reinstall.sh

set -euo pipefail

PROJECT_ROOT="/home/user1/IKAR"
VENV_DIR="${PROJECT_ROOT}/.venv"
DATE_TAG="$(date +%F_%H%M%S)"

info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err()  { echo -e "\033[1;31m[ERR ]\033[0m $*"; }

echo
info "Старт чистки и переустановки окружения (CPU-only)"
info "Проект: ${PROJECT_ROOT}"

info "Размеры до чистки (папки верхнего уровня):"
du -h --max-depth=1 "${PROJECT_ROOT}" | sort -h || true
df -h "${PROJECT_ROOT}" || true

# 1) Опционально остановить PM2 процессы
if [[ "${STOP_PM2:-0}" == "1" ]]; then
  if command -v pm2 >/dev/null 2>&1; then
    info "Останавливаю PM2-процессы туннелей (если запущены)"
    pm2 stop localtunnel-igorhook6666 2>/dev/null || true
    pm2 stop localtunnel-ikar-main 2>/dev/null || true
    pm2 stop tunnel-manager 2>/dev/null || true
  else
    warn "pm2 не найден в PATH — пропускаю остановку PM2"
  fi
fi

# 2) Удаление виртуальных окружений
info "Удаляю виртуальные окружения: ${VENV_DIR} и ${PROJECT_ROOT}/venv"
rm -rf "${VENV_DIR}" "${PROJECT_ROOT}/venv" 2>/dev/null || true

# 3) Очистка логов, временных файлов и отчётов
info "Чищу logs/, temp/, reports/"
rm -rf "${PROJECT_ROOT}/logs"/* "${PROJECT_ROOT}/temp"/* "${PROJECT_ROOT}/reports"/* 2>/dev/null || true

# 4) Удаление кэша байткода Python
info "Удаляю __pycache__ и *.py[co]"
find "${PROJECT_ROOT}" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "${PROJECT_ROOT}" -type f -name "*.py[co]" -delete 2>/dev/null || true

# 5) Node-модули фронтенда (если есть)
if [[ -d "${PROJECT_ROOT}/frontend/node_modules" ]]; then
  info "Удаляю frontend/node_modules"
  rm -rf "${PROJECT_ROOT}/frontend/node_modules"
fi

# 6) Большие .pt модели (silero_tts.pt, yolov8n.pt)
HANDLE_MODELS_MODE="${HANDLE_MODELS:-archive}"
if [[ -f "${PROJECT_ROOT}/silero_tts.pt" || -f "${PROJECT_ROOT}/yolov8n.pt" ]]; then
  case "${HANDLE_MODELS_MODE}" in
    archive)
      info "Архивирую и удаляю крупные модели (.pt)"
      ARCHIVE_PATH="/home/user1/models_backup_${DATE_TAG}.tar.xz"
      tar -cJf "${ARCHIVE_PATH}" -C "${PROJECT_ROOT}" silero_tts.pt yolov8n.pt 2>/dev/null || true
      info "Создан архив: ${ARCHIVE_PATH} (если файлы присутствовали)"
      rm -f "${PROJECT_ROOT}/silero_tts.pt" "${PROJECT_ROOT}/yolov8n.pt" 2>/dev/null || true
      ;;
    delete)
      warn "Удаляю крупные модели (.pt) без архивации по запросу (HANDLE_MODELS=delete)"
      rm -f "${PROJECT_ROOT}/silero_tts.pt" "${PROJECT_ROOT}/yolov8n.pt" 2>/dev/null || true
      ;;
    keep)
      info "Оставляю крупные модели (.pt) (HANDLE_MODELS=keep)"
      ;;
    *)
      warn "Неизвестный режим HANDLE_MODELS='${HANDLE_MODELS_MODE}', использую archive"
      ARCHIVE_PATH="/home/user1/models_backup_${DATE_TAG}.tar.xz"
      tar -cJf "${ARCHIVE_PATH}" -C "${PROJECT_ROOT}" silero_tts.pt yolov8n.pt 2>/dev/null || true
      rm -f "${PROJECT_ROOT}/silero_tts.pt" "${PROJECT_ROOT}/yolov8n.pt" 2>/dev/null || true
      ;;
  esac
fi

# 7) Экспорт/данные (опционально и осторожно)
if [[ "${PURGE_EXPORTED:-0}" == "1" && -d "${PROJECT_ROOT}/exported_memory" ]]; then
  warn "Удаляю exported_memory/* (PURGE_EXPORTED=1)"
  rm -rf "${PROJECT_ROOT}/exported_memory"/* 2>/dev/null || true
fi

if [[ "${PURGE_DATA:-0}" == "1" && -d "${PROJECT_ROOT}/data" ]]; then
  warn "Удаляю data/* (PURGE_DATA=1)"
  rm -rf "${PROJECT_ROOT}/data"/* 2>/dev/null || true
fi

# 8) Бэкапы (по желанию можно сжать)
if [[ "${COMPRESS_BACKUPS:-0}" == "1" && -d "${PROJECT_ROOT}/backups" ]]; then
  info "Сжимаю backups -> ${PROJECT_ROOT}_backups_${DATE_TAG}.tar.xz и удаляю оригинал"
  tar -cJf "${PROJECT_ROOT}_backups_${DATE_TAG}.tar.xz" -C "${PROJECT_ROOT}" backups 2>/dev/null || true
  rm -rf "${PROJECT_ROOT}/backups" 2>/dev/null || true
fi

# 9) Очистка кэшей пакетов (вне проекта тоже много места)
info "Очищаю кэши pip и моделей (в домашней директории)"
python3 -m pip cache purge 2>/dev/null || true
rm -rf "/home/user1/.cache/pip" \
       "/home/user1/.cache/huggingface" \
       "/home/user1/.cache/torch" \
       "/home/user1/.cache/ultralytics" 2>/dev/null || true

# 10) Переустановка окружения (CPU-only PyTorch уже зафиксирован в requirements.txt)
info "Создаю новое виртуальное окружение: ${VENV_DIR}"
python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip cache purge
info "Устанавливаю зависимости без кэша"
"${VENV_DIR}/bin/python" -m pip install --no-cache-dir -r "${PROJECT_ROOT}/requirements.txt"

# 11) Проверка версий FastAPI/Pydantic
info "Проверяю версии FastAPI/Pydantic"
"${VENV_DIR}/bin/python" - <<'PY'
import fastapi, pydantic
print("fastapi", fastapi.__version__)
print("pydantic", pydantic.__version__)
PY

echo
info "Размеры после чистки:"
du -h --max-depth=1 "${PROJECT_ROOT}" | sort -h || true
df -h "${PROJECT_ROOT}" || true

echo
info "Готово. Для локального смоук-теста запустите (в другой сессии):"
echo "  cd ${PROJECT_ROOT}/backend && ../../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 6666 --log-level info"
echo "Завершение: Ctrl+C"


