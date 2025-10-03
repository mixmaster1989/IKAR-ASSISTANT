#!/bin/bash

echo "🔧 Исправление проблемных коммитов"
echo "=================================="

# Создаем резервную копию
echo "📦 Создание резервной копии..."
git stash push -m "backup_before_fix_$(date +%Y%m%d_%H%M%S)"

# Откатываемся к последнему успешному коммиту
echo "⏪ Откат к последнему успешному коммиту..."
git reset --hard efa83972f4aee70796ab665f103c7b944673770d

# Удаляем большие файлы из индекса
echo "🗑️ Удаление больших файлов..."
git rm --cached -r venv_clean/ 2>/dev/null || true
git rm --cached translate-ru_en-1_9.argosmodel 2>/dev/null || true

# Добавляем обновленный .gitignore
echo "📝 Обновление .gitignore..."
git add .gitignore

# Создаем новый коммит без больших файлов
echo "💾 Создание нового коммита..."
git commit -m "Add Git repository cleanup tools and analysis (without large files)"

# Пробуем пуш
echo "🚀 Отправка в GitHub..."
git push origin main

echo "✅ Исправление завершено" 