#!/bin/bash

echo "🚀 Пуш через GitHub CLI"
echo "======================="

# Проверяем, установлен ли GitHub CLI
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI найден"
    
    # Проверяем аутентификацию
    echo "🔐 Проверка аутентификации..."
    gh auth status 2>/dev/null || {
        echo "❌ Не аутентифицирован в GitHub CLI"
        echo "Выполните: gh auth login"
        exit 1
    }
    
    # Делаем пуш
    echo "📤 Отправка изменений..."
    git push origin main
    
else
    echo "❌ GitHub CLI не установлен"
    echo "Установите: sudo apt install gh"
    echo "Или выполните аутентификацию: gh auth login"
fi

echo "✅ Готово" 