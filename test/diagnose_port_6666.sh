#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

function print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
}

echo -e "${YELLOW}==== 1. Проверка Python и pip ====${NC}"
python3 --version && pip3 --version
print_status $?

echo -e "${YELLOW}==== 2. Проверка наличия FastAPI и uvicorn ====${NC}"
pip3 show fastapi && pip3 show uvicorn
print_status $?

echo -e "${YELLOW}==== 3. Проверка структуры проекта ====${NC}"
REQUIRED_FILES=(
    "backend/main.py"
    "frontend/public/admin.html"
    "frontend/public/index.html"
    "frontend/public/app.js"
    "frontend/public/styles.css"
    "requirements.txt"
)
for f in "${REQUIRED_FILES[@]}"; do
    if [ -f $f ]; then
        echo "$f найден"
    else
        echo -e "${RED}$f НЕ найден${NC}"
    fi
done

echo -e "${YELLOW}==== 4. Проверка, запущен ли FastAPI/uvicorn ====${NC}"
ps aux | grep -E 'uvicorn|python.*backend/main.py' | grep -v grep || echo "FastAPI/uvicorn не найден в процессах"

echo -e "${YELLOW}==== 5. Проверка, слушает ли порт 6666 (локально) ====${NC}"
if command -v lsof &> /dev/null; then
    lsof -i :6666 || echo "lsof: порт 6666 не слушается"
elif command -v netstat &> /dev/null; then
    netstat -tuln | grep 6666 || echo "netstat: порт 6666 не слушается"
else
    echo "Нет lsof или netstat для проверки порта."
fi

if command -v ss &> /dev/null; then
    echo -e "${YELLOW}==== Список процессов, слушающих порт 6666 (ss) ===="
    ss -tulnp | grep 6666 || echo "ss: порт 6666 не слушается"
fi

echo -e "${YELLOW}==== 6. Проверка доступности FastAPI через curl (локально) ====${NC}"
if command -v curl &> /dev/null; then
    curl -I --max-time 5 http://127.0.0.1:6666/ || echo "curl: FastAPI не отвечает на 127.0.0.1:6666"
else
    echo "curl не установлен, пропускаю проверку curl."
fi

echo -e "${YELLOW}==== 7. Проверка firewall (ufw, firewalld) ====${NC}"
if command -v ufw &> /dev/null; then
    sudo ufw status | grep 6666 || echo "ufw: порт 6666 не открыт"
fi
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --list-ports | grep 6666 || echo "firewalld: порт 6666 не открыт"
fi

echo -e "${YELLOW}==== 8. Проверка SELinux (если есть) ====${NC}"
if command -v getenforce &> /dev/null; then
    getenforce
fi

echo -e "${YELLOW}==== 9. Проверка, слушает ли внешний IP ====${NC}"
IP=$(hostname -I | awk '{print $1}')
echo "curl -I --max-time 5 http://$IP:6666/"
curl -I --max-time 5 http://$IP:6666/ || echo "curl: FastAPI не отвечает на внешнем IP $IP:6666"

echo -e "${YELLOW}==== 10. Диагностика причин недоступности порта 6666 снаружи ====${NC}"
# Проверка, слушает ли FastAPI на 0.0.0.0
if ps aux | grep -E 'uvicorn|python.*backend/main.py' | grep -v grep | grep '0.0.0.0' > /dev/null; then
    echo -e "FastAPI/uvicorn запущен на 0.0.0.0 (должен быть доступен снаружи)"
else
    echo -e "${RED}ВНИМАНИЕ: FastAPI/uvicorn, возможно, запущен только на 127.0.0.1!${NC}"
    echo -e "Проверьте параметры запуска: должен быть --host 0.0.0.0"
fi

# Проверка, открыт ли порт в firewall
if command -v ufw &> /dev/null; then
    sudo ufw status | grep 6666 > /dev/null || echo -e "${RED}Порт 6666 не открыт в ufw!${NC}"
fi
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --list-ports | grep 6666 > /dev/null || echo -e "${RED}Порт 6666 не открыт в firewalld!${NC}"
fi

# Проверка, слушает ли FastAPI на внешнем IP
if curl -I --max-time 5 http://$IP:6666/ 2>&1 | grep 'Connection refused'; then
    echo -e "${RED}Порт 6666 не слушается на внешнем IP!${NC}"
    echo "Возможные причины:"
    echo "- FastAPI не запущен с --host 0.0.0.0"
    echo "- Порт заблокирован firewall"
    echo "- Проблемы с сетью/маршрутизацией"
fi

echo -e "${YELLOW}==== 11. Подсказки по устранению проблем ====${NC}"
echo "- Если порт не слушается: проверьте логи запуска FastAPI, убедитесь, что порт 6666 не занят другим процессом."
echo "- Если curl не отвечает: проверьте, что FastAPI запущен, и нет ошибок в коде."
echo "- Если порт закрыт firewall: откройте порт 6666 (sudo ufw allow 6666/tcp или через firewalld)."
echo "- Если admin.html не найден: убедитесь, что файл лежит в frontend/public."
echo "- Если SELinux в enforcing: настройте политику или временно переведите в permissive для теста."
echo "- Для доступа снаружи FastAPI должен быть запущен с --host 0.0.0.0"
echo

echo -e "${GREEN}==== Диагностика завершена ====${NC}"