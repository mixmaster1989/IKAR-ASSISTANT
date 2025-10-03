#!/bin/bash

echo "🔍 Диагностика проблем с Git push"
echo "=================================="

echo ""
echo "📊 Текущий статус Git:"
git status

echo ""
echo "🌐 Конфигурация удаленного репозитория:"
git remote -v

echo ""
echo "🔑 Проверка SSH ключей:"
ls -la ~/.ssh/ 2>/dev/null || echo "SSH ключи не найдены"

echo ""
echo "📡 Тест подключения к GitHub:"
ssh -T git@github.com 2>&1 || echo "SSH подключение к GitHub не работает"

echo ""
echo "🔗 Тест HTTPS подключения:"
curl -I https://github.com/mixmaster1989/IKAR.git 2>/dev/null || echo "HTTPS подключение не работает"

echo ""
echo "📝 Последние коммиты:"
git log --oneline -5

echo ""
echo "🚀 Попытка push с подробным выводом:"
git push --verbose origin main

echo ""
echo "✅ Диагностика завершена" 