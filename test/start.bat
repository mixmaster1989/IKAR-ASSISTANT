@echo off
chcp 65001 >nul
cls

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                         ЧАТУМБА                              ║
echo ║                Нестандартный AI-компаньон                    ║
echo ║                     с живой душой                            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/4] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.10+ с python.org
    pause
    exit /b 1
)
echo ✅ Python найден

echo.
echo [2/4] Проверка зависимостей...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Зависимости не установлены. Устанавливаем...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Ошибка установки зависимостей
        pause
        exit /b 1
    )
)
echo ✅ Зависимости готовы

echo.
echo [3/4] Проверка API ключей...
if not exist .env (
    echo ⚠️  Файл .env не найден. Создаем шаблон...
    echo # API ключи > .env
    echo OPENROUTER_API_KEY=your_openrouter_api_key >> .env
    echo EMBEDDING_API_KEY=your_openai_api_key >> .env
    echo TELEGRAM_BOT_TOKEN=your_telegram_bot_token >> .env
    echo.
    echo ❌ Настройте API ключи в файле .env и запустите снова
    echo    Получить ключи:
    echo    - OpenRouter: https://openrouter.ai/
    echo    - OpenAI: https://platform.openai.com/api-keys
    pause
    exit /b 1
)
echo ✅ Файл .env найден

echo.
echo [4/4] Запуск Чатумбы...
echo.
echo 🚀 Запускаем сервер...
echo 🌐 Веб-интерфейс: http://localhost:6666
echo 👤 Панель души: http://localhost:6666/soul.html
echo.
echo Нажмите Ctrl+C для остановки
echo.

cd backend
python main.py
