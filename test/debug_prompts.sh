#!/bin/bash

echo "=== ДИАГНОСТИКА ПРОМПТОВ ==="
echo "Время: $(date)"
echo ""

echo "1. СОДЕРЖИМОЕ admin_prompts.json:"
echo "================================"
if [ -f "backend/admin_prompts.json" ]; then
    cat backend/admin_prompts.json
    echo ""
    echo "Размер файла: $(wc -c < backend/admin_prompts.json) байт"
else
    echo "ФАЙЛ НЕ НАЙДЕН: backend/admin_prompts.json"
fi
echo ""

echo "2. ПРОЦЕССЫ PYTHON:"
echo "==================="
ps aux | grep python | grep -v grep
echo ""

echo "3. ОТКРЫТЫЕ ПОРТЫ:"
echo "=================="
netstat -tlnp 2>/dev/null | grep python || ss -tlnp | grep python
echo ""

echo "4. СТРУКТУРА BACKEND:"
echo "===================="
ls -la backend/ | head -20
echo ""

echo "5. ТЕСТ API ПРОМПТОВ (порт 8000):"
echo "================================="
curl -s -X GET http://localhost:6666/api/admin/prompts || echo "ОШИБКА: API недоступен на порту 6666"
echo ""

echo "6. ТЕСТ API ПРОМПТОВ (порт 5000):"
echo "================================="
curl -s -X GET http://localhost:5000/api/admin/prompts || echo "ОШИБКА: API недоступен на порту 5000"
echo ""

echo "7. ПОСЛЕДНИЕ ЛОГИ (если есть):"
echo "=============================="
if [ -f "nohup.out" ]; then
    echo "=== nohup.out (последние 20 строк) ==="
    tail -20 nohup.out
elif [ -f "app.log" ]; then
    echo "=== app.log (последние 20 строк) ==="
    tail -20 app.log
else
    echo "Логи не найдены (nohup.out, app.log)"
fi
echo ""

echo "=== КОНЕЦ ДИАГНОСТИКИ ==="
