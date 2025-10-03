#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

clear

echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                         ЧАТУМБА                              ║${NC}"
echo -e "${PURPLE}║                Нестандартный AI-компаньон                    ║${NC}"
echo -e "${PURPLE}║                     с живой душой                            ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

echo -e "${BLUE}[1/4] Проверка Python...${NC}"
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python не найден! Установите Python 3.10+${NC}"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi
echo -e "${GREEN}✅ Python найден${NC}"

echo
echo -e "${BLUE}[2/4] Проверка зависимостей...${NC}"
if ! $PYTHON_CMD -c "import fastapi" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Зависимости не установлены. Устанавливаем...${NC}"
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Ошибка установки зависимостей${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ Зависимости готовы${NC}"

echo
echo -e "${BLUE}[3/4] Проверка API ключей...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Файл .env не найден. Создаем шаблон...${NC}"
    cat > .env << EOF
# API ключи
OPENROUTER_API_KEY=your_openrouter_api_key
EMBEDDING_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
EOF
    echo
    echo -e "${RED}❌ Настройте API ключи в файле .env и запустите снова${NC}"
    echo -e "   Получить ключи:"
    echo -e "   - OpenRouter: https://openrouter.ai/"
    echo -e "   - OpenAI: https://platform.openai.com/api-keys"
    exit 1
fi
echo -e "${GREEN}✅ Файл .env найден${NC}"

echo
echo -e "${BLUE}[4/4] Запуск Чатумбы...${NC}"
echo
echo -e "${GREEN}🚀 Запускаем сервер...${NC}"
echo -e "${BLUE}🌐 Веб-интерфейс: http://localhost:6666${NC}"
echo -e "${PURPLE}👤 Панель души: http://localhost:6666/soul.html${NC}"
echo
echo -e "${YELLOW}Нажмите Ctrl+C для остановки${NC}"
echo

cd backend
$PYTHON_CMD main.py
