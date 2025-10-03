#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Установка зависимостей для тестирования LLM API${NC}"
echo "=" * 50

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python не найден! Установите Python 3.8+${NC}"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo -e "${GREEN}✅ Python найден: $($PYTHON_CMD --version)${NC}"

# Устанавливаем openai
echo -e "${BLUE}📦 Устанавливаем библиотеку openai...${NC}"
$PYTHON_CMD -m pip install openai

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ openai установлен успешно${NC}"
else
    echo -e "${RED}❌ Ошибка установки openai${NC}"
    exit 1
fi

# Проверяем установку
echo -e "${BLUE}🔍 Проверяем установку...${NC}"
$PYTHON_CMD -c "import openai; print(f'✅ openai версия: {openai.__version__}')"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Все зависимости установлены!${NC}"
    echo ""
    echo -e "${YELLOW}💡 Теперь можете:${NC}"
    echo -e "   1. Добавить LLM_API=ваш_ключ в .env файл"
    echo -e "   2. Запустить быстрый тест: $PYTHON_CMD test_quick_llm.py"
    echo -e "   3. Запустить полный тест: $PYTHON_CMD test_new_llm_api.py"
else
    echo -e "${RED}❌ Ошибка проверки установки${NC}"
    exit 1
fi
