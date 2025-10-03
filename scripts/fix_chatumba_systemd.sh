#!/usr/bin/env bash
set -euo pipefail

# Авто-фикс systemd-юнита chatumba: правит путь venv -> .venv и перезапускает сервис

PROJECT_DIR="/home/user1/IKAR"
PY_BIN="${PROJECT_DIR}/.venv/bin/python"

echo "[INFO] Проверка интерпретатора: ${PY_BIN}"
if [[ ! -x "${PY_BIN}" ]]; then
  echo "[ERR ] Не найден интерпретатор ${PY_BIN}. Создайте .venv или поправьте путь."
  exit 1
fi

echo "[INFO] Определяю путь юнита..."
UNIT_PATH=$(systemctl show -p FragmentPath chatumba | sed 's/FragmentPath=//')
if [[ -z "${UNIT_PATH}" || ! -f "${UNIT_PATH}" ]]; then
  echo "[ERR ] Не удалось определить путь юнита chatumba. Попробуйте: sudo systemctl cat chatumba"
  exit 1
fi
echo "[INFO] Юнит: ${UNIT_PATH}"

TS=$(date +%F_%H%M%S)
echo "[INFO] Бэкап юнита → ${UNIT_PATH}.bak.${TS}"
sudo cp "${UNIT_PATH}" "${UNIT_PATH}.bak.${TS}"

echo "[INFO] Чиню путь venv → .venv в ExecStart"
# Точный путь и запасной шаблон
sudo sed -i "s|${PROJECT_DIR}/venv/bin/python|${PROJECT_DIR}/.venv/bin/python|g" "${UNIT_PATH}"
sudo sed -i "s|/IKAR/venv/bin/python|/IKAR/.venv/bin/python|g" "${UNIT_PATH}"

echo "[INFO] Текущая строка ExecStart:"
grep -E '^ExecStart=' "${UNIT_PATH}" || true

echo "[INFO] daemon-reload"
sudo systemctl daemon-reload

echo "[INFO] Перезапуск chatumba"
set +e
sudo systemctl restart chatumba
RC=$?
set -e

if [[ ${RC} -ne 0 ]]; then
  echo "[WARN] Перезапуск завершился с кодом ${RC}. Пробую создать symlink venv → .venv (временный фикс)."
  if [[ ! -e "${PROJECT_DIR}/venv" ]]; then
    ln -sfn .venv "${PROJECT_DIR}/venv"
    echo "[INFO] Создан symlink: ${PROJECT_DIR}/venv -> .venv"
  fi
  sudo systemctl restart chatumba || true
fi

echo "[INFO] Статус:"
sudo systemctl status chatumba --no-pager || true

echo "[INFO] Последние логи:"
sudo journalctl -u chatumba -n 80 --no-pager || true

if systemctl is-active --quiet chatumba; then
  echo "[OK  ] Сервис chatumba активен."
  exit 0
else
  echo "[ERR ] Сервис chatumba не активен. Проверьте статус/логи выше."
  exit 2
fi


