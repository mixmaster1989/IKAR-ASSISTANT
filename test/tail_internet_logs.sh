#!/bin/bash
# 🌐 Быстрый просмотр логов системы интернет-интеллекта

LOG_FILE="internet_intelligence.log"

echo "🌐 ПРОСМОТР ЛОГОВ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА"
echo "=================================================="

# Проверяем существование файла логов
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Файл логов $LOG_FILE не найден"
    echo "💡 Убедитесь, что система интернет-интеллекта была запущена"
    exit 1
fi

# Показываем информацию о файле
FILE_SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo "unknown")
FILE_MTIME=$(stat -f%Sm "$LOG_FILE" 2>/dev/null || stat -c%y "$LOG_FILE" 2>/dev/null || echo "unknown")

echo "📁 Файл: $LOG_FILE"
echo "📊 Размер: $FILE_SIZE байт"
echo "⏰ Последнее изменение: $FILE_MTIME"
echo ""

# Функция для показа последних строк
show_last_lines() {
    echo "📝 ПОСЛЕДНИЕ 20 ЗАПИСЕЙ:"
    echo "=================================================="
    tail -n 20 "$LOG_FILE"
}

# Функция для показа ошибок
show_errors() {
    echo "❌ ПОСЛЕДНИЕ ОШИБКИ:"
    echo "=================================================="
    grep "ERROR" "$LOG_FILE" | tail -n 10
}

# Функция для показа поисковых запросов
show_search_requests() {
    echo "🔍 ПОСЛЕДНИЕ ПОИСКОВЫЕ ЗАПРОСЫ:"
    echo "=================================================="
    grep "🔍 ПОИСКОВЫЙ ЗАПРОС" "$LOG_FILE" | tail -n 10
}

# Функция для показа производительности
show_performance() {
    echo "⚡ ПОСЛЕДНИЕ ЗАПИСИ ПРОИЗВОДИТЕЛЬНОСТИ:"
    echo "=================================================="
    grep "⚡ ПРОИЗВОДИТЕЛЬНОСТЬ" "$LOG_FILE" | tail -n 10
}

# Функция для показа Telegram интеграций
show_telegram() {
    echo "📱 ПОСЛЕДНИЕ TELEGRAM ИНТЕГРАЦИИ:"
    echo "=================================================="
    grep "📱 TELEGRAM ИНТЕГРАЦИЯ" "$LOG_FILE" | tail -n 10
}

# Функция для мониторинга в реальном времени
monitor_realtime() {
    echo "🔄 МОНИТОРИНГ В РЕАЛЬНОМ ВРЕМЕНИ (Ctrl+C для выхода):"
    echo "=================================================="
    tail -f "$LOG_FILE"
}

# Функция для статистики
show_stats() {
    echo "📊 СТАТИСТИКА ЛОГОВ:"
    echo "=================================================="
    
    TOTAL_LINES=$(wc -l < "$LOG_FILE")
    ERROR_COUNT=$(grep -c "ERROR" "$LOG_FILE" || echo "0")
    WARNING_COUNT=$(grep -c "WARNING" "$LOG_FILE" || echo "0")
    INFO_COUNT=$(grep -c "INFO" "$LOG_FILE" || echo "0")
    SEARCH_COUNT=$(grep -c "🔍 ПОИСКОВЫЙ ЗАПРОС" "$LOG_FILE" || echo "0")
    TELEGRAM_COUNT=$(grep -c "📱 TELEGRAM ИНТЕГРАЦИЯ" "$LOG_FILE" || echo "0")
    
    echo "📈 Всего строк: $TOTAL_LINES"
    echo "❌ Ошибок: $ERROR_COUNT"
    echo "⚠️  Предупреждений: $WARNING_COUNT"
    echo "ℹ️  Информационных: $INFO_COUNT"
    echo "🔍 Поисковых запросов: $SEARCH_COUNT"
    echo "📱 Telegram интеграций: $TELEGRAM_COUNT"
}

# Основное меню
while true; do
    echo ""
    echo "🎮 МЕНЮ ПРОСМОТРА ЛОГОВ:"
    echo "1. 📝 Последние записи"
    echo "2. ❌ Ошибки"
    echo "3. 🔍 Поисковые запросы"
    echo "4. ⚡ Производительность"
    echo "5. 📱 Telegram интеграции"
    echo "6. 📊 Статистика"
    echo "7. 🔄 Мониторинг в реальном времени"
    echo "8. 🔍 Поиск по ключевому слову"
    echo "0. ❌ Выход"
    echo "----------------------------------------"
    
    read -p "Выберите опцию: " choice
    
    case $choice in
        1)
            show_last_lines
            ;;
        2)
            show_errors
            ;;
        3)
            show_search_requests
            ;;
        4)
            show_performance
            ;;
        5)
            show_telegram
            ;;
        6)
            show_stats
            ;;
        7)
            monitor_realtime
            ;;
        8)
            read -p "Введите ключевое слово для поиска: " keyword
            echo "🔍 ПОИСК ПО КЛЮЧЕВОМУ СЛОВУ '$keyword':"
            echo "=================================================="
            grep "$keyword" "$LOG_FILE" | tail -n 20
            ;;
        0)
            echo "👋 До свидания!"
            exit 0
            ;;
        *)
            echo "❌ Неверный выбор"
            ;;
    esac
    
    echo ""
    read -p "Нажмите Enter для продолжения..."
done 