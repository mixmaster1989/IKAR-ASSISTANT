#!/bin/bash

# 🧠 СКРИПТ ДЛЯ ПРОСМОТРА ЛОГОВ ПРОМПТОВ AI МОДЕЛЕЙ
# Быстрый просмотр и фильтрация логов взаимодействия с AI моделями

LOG_FILE="ai_prompts.log"
VIEWER_SCRIPT="view_ai_prompts_logs.py"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функция для показа заголовка
show_header() {
    echo -e "${CYAN}"
    echo "🧠 ЛОГИ ПРОМПТОВ AI МОДЕЛЕЙ"
    echo "================================"
    echo -e "${NC}"
}

# Функция для показа меню
show_menu() {
    echo -e "${YELLOW}Выберите действие:${NC}"
    echo "1)  Последние записи (tail)"
    echo "2)  Сводка статистики"
    echo "3)  Последние промпты"
    echo "4)  Последние ответы"
    echo "5)  Ошибки"
    echo "6)  Производительность"
    echo "7)  Поиск по логам"
    echo "8)  Полный промпт по ID"
    echo "9)  Мониторинг в реальном времени"
    echo "10) Статистика по моделям"
    echo "11) Анализ качества промптов"
    echo "12) Экспорт логов"
    echo "0)  Выход"
    echo ""
}

# Функция для проверки существования файла логов
check_log_file() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}❌ Файл логов не найден: $LOG_FILE${NC}"
        echo "Создайте файл логов или укажите правильный путь"
        return 1
    fi
    return 0
}

# Функция для показа последних записей
show_tail() {
    echo -e "${GREEN}📄 Последние записи логов:${NC}"
    echo ""
    if command -v tail &> /dev/null; then
        tail -n 20 "$LOG_FILE" | while IFS= read -r line; do
            if [[ $line == *"🧠 AI ЗАПРОС:"* ]]; then
                echo -e "${BLUE}$line${NC}"
            elif [[ $line == *"✅ AI ОТВЕТ:"* ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ $line == *"❌ AI ОШИБКА:"* ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ $line == *"⚡ AI ПРОИЗВОДИТЕЛЬНОСТЬ:"* ]]; then
                echo -e "${YELLOW}$line${NC}"
            else
                echo "$line"
            fi
        done
    else
        echo -e "${RED}❌ Команда tail не найдена${NC}"
    fi
}

# Функция для показа сводки
show_summary() {
    echo -e "${GREEN}📊 Сводка статистики:${NC}"
    echo ""
    if [ -f "$VIEWER_SCRIPT" ]; then
        python3 "$VIEWER_SCRIPT" --action summary
    else
        echo -e "${RED}❌ Скрипт просмотра не найден: $VIEWER_SCRIPT${NC}"
    fi
}

# Функция для показа последних промптов
show_prompts() {
    echo -e "${GREEN}🧠 Последние промпты:${NC}"
    echo ""
    if [ -f "$VIEWER_SCRIPT" ]; then
        python3 "$VIEWER_SCRIPT" --action prompts --count 10
    else
        echo -e "${RED}❌ Скрипт просмотра не найден${NC}"
    fi
}

# Функция для показа последних ответов
show_responses() {
    echo -e "${GREEN}💬 Последние ответы:${NC}"
    echo ""
    if [ -f "$VIEWER_SCRIPT" ]; then
        python3 "$VIEWER_SCRIPT" --action responses --count 10
    else
        echo -e "${RED}❌ Скрипт просмотра не найден${NC}"
    fi
}

# Функция для показа ошибок
show_errors() {
    echo -e "${GREEN}❌ Последние ошибки:${NC}"
    echo ""
    if [ -f "$VIEWER_SCRIPT" ]; then
        python3 "$VIEWER_SCRIPT" --action errors --count 10
    else
        echo -e "${RED}❌ Скрипт просмотра не найден${NC}"
    fi
}

# Функция для показа производительности
show_performance() {
    echo -e "${GREEN}⚡ Производительность:${NC}"
    echo ""
    if [ -f "$VIEWER_SCRIPT" ]; then
        python3 "$VIEWER_SCRIPT" --action performance --hours 24
    else
        echo -e "${RED}❌ Скрипт просмотра не найден${NC}"
    fi
}

# Функция для поиска
search_logs() {
    echo -e "${GREEN}🔍 Поиск в логах:${NC}"
    echo ""
    read -p "Введите поисковый запрос: " query
    if [ -n "$query" ]; then
        if [ -f "$VIEWER_SCRIPT" ]; then
            python3 "$VIEWER_SCRIPT" --action search --query "$query"
        else
            echo -e "${RED}❌ Скрипт просмотра не найден${NC}"
        fi
    else
        echo -e "${YELLOW}❌ Поисковый запрос не может быть пустым${NC}"
    fi
}

# Функция для показа полного промпта
show_full_prompt() {
    echo -e "${GREEN}📄 Полный промпт:${NC}"
    echo ""
    read -p "Введите ID запроса: " request_id
    if [ -n "$request_id" ]; then
        if [ -f "$VIEWER_SCRIPT" ]; then
            python3 "$VIEWER_SCRIPT" --action full --request-id "$request_id"
        else
            echo -e "${RED}❌ Скрипт просмотра не найден${NC}"
        fi
    else
        echo -e "${YELLOW}❌ ID запроса не может быть пустым${NC}"
    fi
}

# Функция для мониторинга в реальном времени
monitor_realtime() {
    echo -e "${GREEN}📡 Мониторинг в реальном времени:${NC}"
    echo "Нажмите Ctrl+C для остановки"
    echo ""
    if command -v tail &> /dev/null; then
        tail -f "$LOG_FILE" | while IFS= read -r line; do
            if [[ $line == *"🧠 AI ЗАПРОС:"* ]]; then
                echo -e "${BLUE}$line${NC}"
            elif [[ $line == *"✅ AI ОТВЕТ:"* ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ $line == *"❌ AI ОШИБКА:"* ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ $line == *"⚡ AI ПРОИЗВОДИТЕЛЬНОСТЬ:"* ]]; then
                echo -e "${YELLOW}$line${NC}"
            else
                echo "$line"
            fi
        done
    else
        echo -e "${RED}❌ Команда tail не найдена${NC}"
    fi
}

# Функция для статистики по моделям
show_model_stats() {
    echo -e "${GREEN}🤖 Статистика по моделям:${NC}"
    echo ""
    if [ -f "$LOG_FILE" ]; then
        echo "Использованные модели:"
        grep "Модель:" "$LOG_FILE" | cut -d'|' -f5 | sed 's/.*Модель: //' | sort | uniq -c | sort -nr
        echo ""
        echo "Последние модели:"
        grep "Модель:" "$LOG_FILE" | tail -10 | cut -d'|' -f1,5 | sed 's/|.*Модель: /: /'
    else
        echo -e "${RED}❌ Файл логов не найден${NC}"
    fi
}

# Функция для анализа качества промптов
analyze_quality() {
    echo -e "${GREEN}📊 Анализ качества промптов:${NC}"
    echo ""
    if [ -f "$LOG_FILE" ]; then
        echo "Статистика по типам операций:"
        grep -E "(AI ЗАПРОС|AI ОТВЕТ|AI ОШИБКА|AI ПРОИЗВОДИТЕЛЬНОСТЬ)" "$LOG_FILE" | \
        sed 's/.*🧠 AI ЗАПРОС:/Запросы:/' | \
        sed 's/.*✅ AI ОТВЕТ:/Успешные ответы:/' | \
        sed 's/.*❌ AI ОТВЕТ:/Ошибки ответов:/' | \
        sed 's/.*❌ AI ОШИБКА:/Ошибки:/' | \
        sed 's/.*⚡ AI ПРОИЗВОДИТЕЛЬНОСТЬ:/Производительность:/' | \
        cut -d'|' -f1 | sort | uniq -c | sort -nr
        
        echo ""
        echo "Время обработки (последние 10):"
        grep "Время обработки:" "$LOG_FILE" | tail -10 | cut -d'|' -f1,5 | sed 's/|.*Время обработки: /: /'
        
        echo ""
        echo "Использование токенов (последние 10):"
        grep "Токенов использовано:" "$LOG_FILE" | tail -10 | cut -d'|' -f1,5 | sed 's/|.*Токенов использовано: /: /'
    else
        echo -e "${RED}❌ Файл логов не найден${NC}"
    fi
}

# Функция для экспорта логов
export_logs() {
    echo -e "${GREEN}📤 Экспорт логов:${NC}"
    echo ""
    read -p "Введите имя файла для экспорта (без расширения): " export_name
    if [ -n "$export_name" ]; then
        timestamp=$(date +"%Y%m%d_%H%M%S")
        export_file="${export_name}_${timestamp}.txt"
        
        echo "Экспортирую логи в $export_file..."
        
        {
            echo "ЭКСПОРТ ЛОГОВ ПРОМПТОВ AI - $(date)"
            echo "========================================"
            echo ""
            
            if [ -f "$VIEWER_SCRIPT" ]; then
                echo "СВОДКА СТАТИСТИКИ:"
                python3 "$VIEWER_SCRIPT" --action summary
                echo ""
                echo "ПОСЛЕДНИЕ ПРОМПТЫ:"
                python3 "$VIEWER_SCRIPT" --action prompts --count 20
                echo ""
                echo "ПОСЛЕДНИЕ ОТВЕТЫ:"
                python3 "$VIEWER_SCRIPT" --action responses --count 20
                echo ""
                echo "ОШИБКИ:"
                python3 "$VIEWER_SCRIPT" --action errors --count 20
            fi
            
            echo ""
            echo "ПОЛНЫЕ ЛОГИ:"
            echo "============"
            if [ -f "$LOG_FILE" ]; then
                cat "$LOG_FILE"
            fi
        } > "$export_file"
        
        echo -e "${GREEN}✅ Логи экспортированы в $export_file${NC}"
    else
        echo -e "${YELLOW}❌ Имя файла не может быть пустым${NC}"
    fi
}

# Основной цикл
main() {
    show_header
    
    if ! check_log_file; then
        return 1
    fi
    
    while true; do
        show_menu
        read -p "Введите номер (0-12): " choice
        
        case $choice in
            1)
                show_tail
                ;;
            2)
                show_summary
                ;;
            3)
                show_prompts
                ;;
            4)
                show_responses
                ;;
            5)
                show_errors
                ;;
            6)
                show_performance
                ;;
            7)
                search_logs
                ;;
            8)
                show_full_prompt
                ;;
            9)
                monitor_realtime
                ;;
            10)
                show_model_stats
                ;;
            11)
                analyze_quality
                ;;
            12)
                export_logs
                ;;
            0)
                echo -e "${GREEN}👋 До свидания!${NC}"
                break
                ;;
            *)
                echo -e "${RED}❌ Неверный выбор. Попробуйте снова.${NC}"
                ;;
        esac
        
        echo ""
        read -p "Нажмите Enter для продолжения..."
        clear
        show_header
    done
}

# Запуск основного цикла
main "$@" 