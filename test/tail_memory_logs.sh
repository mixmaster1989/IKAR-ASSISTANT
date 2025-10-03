#!/bin/bash

# Скрипт для просмотра логов инъекции памяти в реальном времени

echo "🧠 Мониторинг логов инъекции памяти"
echo "=================================="
echo ""

# Проверяем существование лог-файлов
if [ -f "logs/chatumba.log" ]; then
    echo "📄 Найден основной лог: logs/chatumba.log"
else
    echo "❌ Основной лог не найден"
fi

if [ -f "logs/memory.log" ]; then
    echo "📄 Найден лог памяти: logs/memory.log"
else
    echo "❌ Лог памяти не найден"
fi

echo ""
echo "🔍 Фильтры для просмотра:"
echo "1. Все логи инъекции памяти:"
echo "   tail -f logs/chatumba.log | grep -i 'инъекция\|память\|memory'"
echo ""
echo "2. Только статистика памяти:"
echo "   tail -f logs/chatumba.log | grep -E 'Инъекция памяти|Память инъектирована|чанков|токенов|релевантность'"
echo ""
echo "3. Ошибки памяти:"
echo "   tail -f logs/chatumba.log | grep -i 'ошибка.*память\|error.*memory'"
echo ""
echo "4. Все логи памяти:"
echo "   tail -f logs/memory.log"
echo ""

# Автоматически запускаем мониторинг
echo "🚀 Запускаем мониторинг логов инъекции памяти..."
echo "Нажмите Ctrl+C для остановки"
echo ""

# Показываем последние записи о памяти
echo "📋 Последние записи о памяти:"
if [ -f "logs/chatumba.log" ]; then
    echo "Из chatumba.log:"
    tail -n 20 logs/chatumba.log | grep -i "инъекция\|память\|memory" || echo "   Записей о памяти не найдено"
    echo ""
fi

if [ -f "logs/memory.log" ]; then
    echo "Из memory.log:"
    tail -n 10 logs/memory.log || echo "   Лог памяти пуст"
    echo ""
fi

# Запускаем мониторинг в реальном времени
echo "🔄 Мониторинг в реальном времени:"
echo "=================================="

# Функция для мониторинга
monitor_memory_logs() {
    if [ -f "logs/chatumba.log" ]; then
        tail -f logs/chatumba.log | grep --line-buffered -E "Инъекция памяти|Память инъектирована|чанков|токенов|релевантность|memory_injector|collective_mind" &
    fi
    
    if [ -f "logs/memory.log" ]; then
        tail -f logs/memory.log &
    fi
    
    # Ждем сигнала прерывания
    wait
}

# Запускаем мониторинг
monitor_memory_logs 