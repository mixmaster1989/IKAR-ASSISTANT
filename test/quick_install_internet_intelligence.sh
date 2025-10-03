#!/bin/bash

# 🚀 БЫСТРАЯ УСТАНОВКА ИНТЕРНЕТ-ИНТЕЛЛЕКТА ДЛЯ IKAR

echo "🌐 УСТАНОВКА ИНТЕРНЕТ-ИНТЕЛЛЕКТА ДЛЯ IKAR"
echo "=========================================="

# Проверяем, что мы в правильной директории
if [ ! -f "README.md" ]; then
    echo "❌ README.md не найден. Убедитесь, что вы в корне проекта IKAR."
    exit 1
fi

echo "📦 Устанавливаем зависимости..."

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "🔧 Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем минимальные зависимости
echo "📥 Устанавливаем основные зависимости..."
pip install aiohttp requests beautifulsoup4 lxml feedparser flask python-dotenv

# Пробуем установить дополнительные зависимости
echo "📥 Устанавливаем дополнительные зависимости..."
pip install trafilatura newspaper3k 2>/dev/null || echo "⚠️  Некоторые зависимости не установлены, но система будет работать"

# Создаем папку для данных
echo "📁 Создаем папку для данных..."
mkdir -p data

# Копируем файлы в нужные места
echo "📋 Копируем файлы..."

# Основные файлы
cp internet_intelligence_system_fixed.py backend/internet_intelligence_system.py 2>/dev/null || echo "⚠️  Файл internet_intelligence_system_fixed.py не найден"
cp ikar_internet_integration.py backend/ 2>/dev/null || echo "⚠️  Файл ikar_internet_integration.py не найден"
cp integrate_with_ikar.py backend/ 2>/dev/null || echo "⚠️  Файл integrate_with_ikar.py не найден"
cp internet_api.py backend/api/ 2>/dev/null || echo "⚠️  Файл internet_api.py не найден"

# Тестовые файлы
cp test_internet_intelligence.py ./ 2>/dev/null || echo "⚠️  Файл test_internet_intelligence.py не найден"
cp run_internet_intelligence.py ./ 2>/dev/null || echo "⚠️  Файл run_internet_intelligence.py не найден"

# Обновляем requirements.txt
echo "📝 Обновляем requirements.txt..."
if [ -f "requirements.txt" ]; then
    if ! grep -q "Интернет-интеллект" requirements.txt; then
        echo "" >> requirements.txt
        echo "# Интернет-интеллект" >> requirements.txt
        echo "aiohttp>=3.8.0" >> requirements.txt
        echo "beautifulsoup4>=4.11.0" >> requirements.txt
        echo "feedparser>=6.0.0" >> requirements.txt
        echo "flask>=2.3.0" >> requirements.txt
        echo "python-dotenv>=1.0.0" >> requirements.txt
    fi
fi

echo "✅ Установка завершена!"
echo ""
echo "🧪 Для тестирования выполните:"
echo "   python run_internet_intelligence.py"
echo ""
echo "🚀 Для запуска IKAR с интернет-интеллектом:"
echo "   python run_ikar_with_internet.py"
echo ""
echo "🌐 Веб-интерфейс:"
echo "   http://localhost:6666/internet-intelligence.html" 