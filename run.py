"""
Скрипт для запуска проекта Чатумба.
"""
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Проверяет наличие необходимых зависимостей."""
    try:
        import fastapi
        import uvicorn
        import dotenv
        print("✅ Основные зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствуют зависимости: {e}")
        print("Установите зависимости с помощью команды: pip install -r requirements.txt")
        return False

def load_env():
    """Загружает переменные окружения из .env файла."""
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / '.env'
        load_dotenv(env_path)
        print("✅ Переменные окружения загружены")
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке переменных окружения: {e}")
        print("Создайте файл .env с необходимыми API ключами")

def start_backend():
    """Запускает бэкенд."""
    backend_path = Path(__file__).parent / 'backend'
    os.chdir(backend_path)
    
    print("🚀 Запуск бэкенда...")
    
    # Запускаем бэкенд в отдельном процессе
    if sys.platform == 'win32':
        backend_process = subprocess.Popen(
            ["python", "main.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        backend_process = subprocess.Popen(
            ["python", "main.py"]
        )
    
    # Даем время на запуск
    time.sleep(2)
    
    return backend_process

def open_browser():
    """Открывает браузер с веб-интерфейсом."""
    print("🌐 Открываем веб-интерфейс...")
    webbrowser.open("http://localhost:6666")

def main():
    """Основная функция."""
    print("=" * 50)
    print("Запуск Чатумбы - нестандартного AI-компаньона")
    print("=" * 50)
    
    if not check_dependencies():
        return
    
    load_env()
    
    backend_process = start_backend()
    
    try:
        # Даем время на запуск сервера
        time.sleep(3)
        open_browser()
        
        print("\n✨ Чатумба запущена!")
        print("Веб-интерфейс доступен по адресу: http://localhost:6666")
        print("\nНажмите Ctrl+C для завершения...")
        
        # Ждем, пока пользователь не нажмет Ctrl+C
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n⏹️ Завершение работы...")
        backend_process.terminate()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        backend_process.terminate()

if __name__ == "__main__":
    main()
