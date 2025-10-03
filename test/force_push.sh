#!/bin/bash

echo "🚀 Принудительный пуш в GitHub"
echo "=============================="

# Проверяем статус
echo "📊 Статус Git:"
git status

echo ""
echo "🌐 URL репозитория:"
git remote get-url origin

echo ""
echo "🔧 Попытка пуш с токеном (если настроен):"
# Попробуем пуш с токеном в URL
GIT_URL=$(git remote get-url origin)
if [[ $GIT_URL == https://* ]]; then
    echo "Используем HTTPS URL"
    git push origin main
else
    echo "Переключаемся на HTTPS"
    git remote set-url origin https://github.com/mixmaster1989/IKAR.git
    git push origin main
fi

echo ""
echo "✅ Пуш завершен" 