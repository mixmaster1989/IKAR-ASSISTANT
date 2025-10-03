#!/usr/bin/env python3
"""
Скрипт для автоматического исправления системы IKAR
Исправляет основные проблемы с Flask -> FastAPI миграцией
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_step(step, description):
    """Красивый вывод шага"""
    print(f"\n{'='*60}")
    print(f"🔧 ШАГ {step}: {description}")
    print(f"{'='*60}")

def backup_file(file_path):
    """Создание резервной копии файла"""
    backup_path = f"{file_path}.backup"
    if Path(file_path).exists():
        shutil.copy2(file_path, backup_path)
        print(f"✅ Создана резервная копия: {backup_path}")
        return True
    return False

def fix_main_py():
    """Исправление main.py - замена Flask на FastAPI"""
    print_step(1, "ИСПРАВЛЕНИЕ MAIN.PY")
    
    main_path = Path("backend/main.py")
    if not main_path.exists():
        print("❌ Файл backend/main.py не найден!")
        return False
    
    # Создаем резервную копию
    backup_file(main_path)
    
    # Читаем текущий файл
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, есть ли Flask импорты
    if 'from flask import' not in content:
        print("✅ Файл уже использует FastAPI")
        return True
    
    # Новый контент для main.py
    new_content = '''"""
Основной модуль приложения IKAR - инициализация и запуск всех компонентов
"""

import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from config import Config
from core.collective_mind import initialize_collective_mind
from api.collective_api import collective_router
from api.memory_api import memory_router

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    logging.info("✅ Переменные окружения загружены из .env")
except Exception as e:
    logging.warning(f"⚠️ Ошибка при загрузке переменных окружения: {e}")

from config import API_CONFIG
from api.routes import router
from api.telegram import init_telegram_bot, admin_router as telegram_admin_router
from api.admin_api import admin_router
from api.admin_triggers_autoposts import router as triggers_autoposts_router
from api.admin_logs import router as logs_router
from api.bingx_test_routes import router as bingx_test_router
from api.telegram_voice import get_tts_engine, get_stt_engine  # Новые модули

# Настройка логирования
from utils.logger import setup_logging
setup_logging()

# Создаем экземпляр FastAPI
app = FastAPI(
    title="Chatumba API",
    description="API для взаимодействия с Чатумбой",
    version="0.1.0"
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(triggers_autoposts_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(bingx_test_router, prefix="/api")
app.include_router(telegram_admin_router, prefix="/api")

# Подключаем коллективный разум и систему памяти
app.include_router(collective_router, prefix="/api")
app.include_router(memory_router, prefix="/api")

# Инициализируем Telegram бота (новая модульная версия)
init_telegram_bot(app)

# Применяем патчи для улучшения работы с группами
try:
    from api.telegram_group_patch import apply_group_patches
    apply_group_patches()
    logging.info("✅ Патчи для групп успешно применены")
except Exception as e:
    logging.error(f"❌ Ошибка при применении патчей для групп: {e}")

# Папка для статических файлов
static_dir = Path(__file__).parent.parent / "frontend" / "public"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Папка для временных файлов
temp_dir = Path(__file__).parent.parent / "temp"
temp_dir.mkdir(exist_ok=True)

# Маршрут для аудио файлов
@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """
    Возвращает аудио файл по имени.
    """
    file_path = temp_dir / filename
    if not file_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "Файл не найден"}
        )
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
    )

# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Глобальный обработчик исключений.
    """
    logging.error(f"Ошибка при обработке запроса {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )

async def initialize_systems():
    """Инициализация всех систем"""
    config = Config()
    
    # Инициализация коллективного разума
    try:
        collective_mind = await initialize_collective_mind(config)
        logging.info("Коллективный разум успешно инициализирован")
        
        # Запуск демона синхронизации
        asyncio.create_task(collective_mind.start_sync_daemon())
        
    except Exception as e:
        logging.error(f"Ошибка инициализации коллективного разума: {e}")
    
    # Выводим информацию о ключах OpenRouter
    from config import OPENROUTER_API_KEYS
    print(f"🔑 Найдено API ключей OpenRouter: {len(OPENROUTER_API_KEYS)}")
    for i, key in enumerate(OPENROUTER_API_KEYS, 1):
        key_suffix = key[-10:] if len(key) > 10 else key
        print(f"   Ключ {i}: ...{key_suffix}")
    
    if not OPENROUTER_API_KEYS:
        print("⚠️  ВНИМАНИЕ: API ключи OpenRouter не найдены!")
        print("   Добавьте переменные OPENROUTER_API_KEY, OPENROUTER_API_KEY2, и т.д. в файл .env")
    
    # Выводим информацию о ключах BingX
    from config import BINGX_API_KEY, BINGX_SECRET_KEY
    if BINGX_API_KEY and BINGX_SECRET_KEY:
        print(f"📈 BingX API настроен:")
        print(f"   API Key: ...{BINGX_API_KEY[-8:] if len(BINGX_API_KEY) > 8 else BINGX_API_KEY}")
        print(f"   Secret Key: ...{BINGX_SECRET_KEY[-8:] if len(BINGX_SECRET_KEY) > 8 else BINGX_SECRET_KEY}")
    else:
        print("⚠️  BingX API ключи не настроены!")
        print("   Добавьте BINGX_API_KEY и BINGX_SECRET_KEY в файл .env для полной функциональности")

@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    await initialize_systems()

if __name__ == "__main__":
    import uvicorn
    config = Config()
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )
'''
    
    # Записываем новый контент
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Файл backend/main.py успешно обновлен!")
    return True

def check_and_create_missing_files():
    """Проверка и создание недостающих файлов"""
    print_step(2, "ПРОВЕРКА НЕДОСТАЮЩИХ ФАЙЛОВ")
    
    # Проверяем config.py
    config_path = Path("backend/config.py")
    if not config_path.exists():
        print("⚠️ Файл config.py не найден, создаем...")
        config_content = '''"""
Конфигурация приложения IKAR
"""

import os
from pathlib import Path

class Config:
    """Класс конфигурации приложения"""
    
    def __init__(self):
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", 6666))
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        
        # Пути
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.TEMP_DIR = self.BASE_DIR / "temp"
        
        # Создаем директории
        self.DATA_DIR.mkdir(exist_ok=True)
        self.TEMP_DIR.mkdir(exist_ok=True)
        
        # Коллективный разум
        self.COLLECTIVE_MIND_DB = self.DATA_DIR / "collective_mind.db"
        self.SYNC_INTERVAL = int(os.getenv("COLLECTIVE_SYNC_INTERVAL", "300"))
        self.MAX_MEMORIES_PER_SYNC = int(os.getenv("MAX_MEMORIES_PER_SYNC", "50"))

# Загружаем конфигурацию из переменных окружения
API_CONFIG = {
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", 6666)),
    "debug": os.getenv("DEBUG", "false").lower() == "true"
}

# OpenRouter API ключи
OPENROUTER_API_KEYS = []
for i in range(1, 11):  # Поддержка до 10 ключей
    key_name = f"OPENROUTER_API_KEY{i if i > 1 else ''}"
    key_value = os.getenv(key_name)
    if key_value:
        OPENROUTER_API_KEYS.append(key_value)

# BingX API
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET_KEY = os.getenv("BINGX_SECRET_KEY")
'''
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ Файл config.py создан")
    else:
        print("✅ Файл config.py найден")
    
    # Проверяем core/collective_mind.py
    collective_path = Path("backend/core/collective_mind.py")
    if not collective_path.exists():
        print("⚠️ Файл collective_mind.py не найден, создаем заглушку...")
        collective_path.parent.mkdir(exist_ok=True)
        
        collective_content = '''"""
Заглушка для коллективного разума
"""

import asyncio
import logging

class CollectiveMind:
    """Заглушка для коллективного разума"""
    
    def __init__(self, config):
        self.config = config
        
    async def start_sync_daemon(self):
        """Запуск демона синхронизации"""
        logging.info("Демон синхронизации коллективного разума запущен")
        
async def initialize_collective_mind(config):
    """Инициализация коллективного разума"""
    return CollectiveMind(config)
'''
        
        with open(collective_path, 'w', encoding='utf-8') as f:
            f.write(collective_content)
        print("✅ Файл collective_mind.py создан")
    else:
        print("✅ Файл collective_mind.py найден")

def update_requirements():
    """Обновление requirements.txt"""
    print_step(3, "ОБНОВЛЕНИЕ REQUIREMENTS.TXT")
    
    req_path = Path("requirements.txt")
    if not req_path.exists():
        print("❌ Файл requirements.txt не найден!")
        return False
    
    # Читаем текущие требования
    with open(req_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Удаляем Flask если есть
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if line.strip() and not line.strip().startswith('#'):
            if 'flask' in line.lower() and 'flask' == line.strip().split('=')[0].split('>')[0].split('<')[0].lower():
                print(f"❌ Удаляем Flask: {line}")
                continue
        new_lines.append(line)
    
    # Проверяем наличие необходимых пакетов
    required_packages = [
        'fastapi>=0.95.0',
        'uvicorn[standard]>=0.20.0',
        'pydantic>=2.0.0',
        'starlette>=0.27.0',
        'typing-extensions>=4.0.0'
    ]
    
    content_lower = content.lower()
    for package in required_packages:
        package_name = package.split('>=')[0].split('==')[0]
        if package_name not in content_lower:
            print(f"✅ Добавляем пакет: {package}")
            new_lines.append(package)
    
    # Записываем обновленный файл
    with open(req_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ Файл requirements.txt обновлен")
    return True

def install_dependencies():
    """Установка зависимостей"""
    print_step(4, "УСТАНОВКА ЗАВИСИМОСТЕЙ")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Зависимости установлены успешно")
            return True
        else:
            print(f"❌ Ошибка установки зависимостей: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при установке зависимостей: {e}")
        return False

def test_imports():
    """Тестирование импортов"""
    print_step(5, "ТЕСТИРОВАНИЕ ИМПОРТОВ")
    
    test_modules = ['fastapi', 'uvicorn', 'pydantic', 'starlette']
    
    for module in test_modules:
        try:
            __import__(module)
            print(f"✅ {module} импортируется успешно")
        except ImportError as e:
            print(f"❌ {module} НЕ ИМПОРТИРУЕТСЯ: {e}")
            return False
    
    return True

def main():
    """Основная функция исправления"""
    print("🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ СИСТЕМЫ IKAR")
    print("=" * 60)
    
    success = True
    
    # Выполняем все шаги
    if not fix_main_py():
        success = False
    
    check_and_create_missing_files()
    
    if not update_requirements():
        success = False
    
    if not install_dependencies():
        success = False
    
    if not test_imports():
        success = False
    
    print_step("ФИНАЛ", "РЕЗУЛЬТАТ ИСПРАВЛЕНИЯ")
    
    if success:
        print("✅ ВСЕ ИСПРАВЛЕНИЯ ВЫПОЛНЕНЫ УСПЕШНО!")
        print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. sudo systemctl restart chatumba")
        print("2. sudo journalctl -u chatumba -f")
        print("3. Проверьте работу системы")
    else:
        print("❌ НЕКОТОРЫЕ ИСПРАВЛЕНИЯ НЕ УДАЛИСЬ!")
        print("\n🔍 РЕКОМЕНДАЦИИ:")
        print("1. Проверьте логи выше")
        print("2. Запустите diagnose_system.py для диагностики")
        print("3. Обратитесь за помощью")

if __name__ == "__main__":
    main() 