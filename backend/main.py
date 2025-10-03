"""
🚀 Главный файл запуска IKAR с интеграцией новой системы памяти
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавляем путь к backend в sys.path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Импорты API
from api import routes
from api.admin_api import admin_router
from api.telegram_polling import start_telegram_polling

# Импорт новой системы памяти
from memory.memory_integration import initialize_smart_memory_system
from utils.component_manager import get_component_manager

# Настройка логирования
import os
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    handlers=[
        logging.FileHandler('logs/chatumba.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("chatumba.main")

# Создание FastAPI приложения
app = FastAPI(
    title="IKAR (Чатумба) API",
    description="AI Компаньон с Душой и Умной Памятью",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(routes.router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# Статические файлы
frontend_path = Path(__file__).parent.parent / "frontend" / "public"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("🚀 Запуск IKAR (Чатумба) v2.0.0")
    
    try:
        # Создаем необходимые директории
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Инициализируем новую систему памяти
        logger.info("🧠 Инициализация системы умной памяти...")
        await initialize_smart_memory_system()
        logger.info("✅ Система умной памяти инициализирована")
        
        # Загружаем все существующие сообщения из групп
        logger.info("📚 Загрузка существующих сообщений из групп...")
        from memory.startup_memory_loader import initialize_memory_from_existing_groups
        loader = await initialize_memory_from_existing_groups()
        stats = await loader.get_loading_stats()
        logger.info(f"✅ Загружено: {stats['processed_messages']} сообщений, {stats['created_chunks']} чанков из {stats['total_chats']} чатов")
        logger.info(f"📋 Обработанные чаты: {stats['processed_chats']}")
        
        # Запускаем Telegram polling
        logger.info("📱 Запуск Telegram polling...")
        asyncio.create_task(start_telegram_polling())
        logger.info("✅ Telegram polling запущен")
        
        logger.info("🎉 IKAR полностью инициализирован и готов к работе!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    logger.info("🛑 Завершение работы IKAR...")
    
    try:
        # Останавливаем ночную оптимизацию
        from memory.memory_integration import get_memory_integration
        integration = get_memory_integration()
        integration.stop_optimization()
        
        logger.info("✅ IKAR завершил работу корректно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении: {e}")

@app.get("/")
async def root():
    """Главная страница"""
    return {"message": "IKAR (Чатумба) API v2.0.0 с Умной Памятью"}

@app.get("/api/startup/loader/stats")
async def get_startup_loader_stats():
    """Получает статистику загрузчика при запуске"""
    try:
        from memory.startup_memory_loader import get_startup_loader
        loader = get_startup_loader()
        stats = await loader.get_loading_stats()
        
        from memory.memory_integration import get_memory_integration
        integration = get_memory_integration()
        memory_stats = await integration.get_memory_stats()
        
        return {
            "status": "success",
            "loader_stats": stats,
            "memory_stats": memory_stats
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    try:
        from memory.memory_integration import get_memory_integration
        integration = get_memory_integration()
        
        if integration.initialized:
            memory_stats = await integration.get_memory_stats()
            return {
                "status": "healthy",
                "version": "2.0.0",
                "memory_system": "active",
                "memory_stats": memory_stats
            }
        else:
            return {
                "status": "initializing",
                "version": "2.0.0",
                "memory_system": "initializing"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "version": "2.0.0",
            "error": str(e)
        }

@app.get("/health/llm")
async def health_llm():
    """Проверка доступности LLM через OpenRouter.

    Возвращает статус и короткий ответ модели на пинг.
    """
    try:
        cm = get_component_manager()
        llm = cm.get_llm_client()
        if not llm:
            return {"status": "error", "error": "LLM client not initialized"}

        # Минимальный быстрый вызов
        response = await llm.chat_completion(
            user_message="ping",
            system_prompt="healthcheck",
            temperature=0.0,
            max_tokens=64,
        )
        return {"status": "ok", "response": response[:200] if response else None}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/health/llm")
async def api_health_llm():
    """Дублирование health LLM под префиксом /api, чтобы избежать конфликтов со статикой."""
    return await health_llm()

if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=6767,
        reload=False,
        log_level="info"
    )
