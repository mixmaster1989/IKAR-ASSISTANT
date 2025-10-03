"""
Централизованная система логирования для всего проекта.
"""
import logging
import sys
from pathlib import Path

def setup_logging():
    """Настраивает логирование для всего проекта."""
    
    # Защита от повторной инициализации
    root_logger = logging.getLogger()
    if hasattr(setup_logging, '_initialized') and setup_logging._initialized:
        return  # Логирование уже настроено
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Консольный хендлер
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # Файловый хендлер
    log_file = Path(__file__).parent.parent / "chatumba_debug.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Настраиваем root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Специальные логгеры для модулей
    loggers = [
        'chatumba.telegram',
        'chatumba.telegram_main', 
        'chatumba.personality',
        'chatumba.vision',
        'chatumba.llm',
        'chatumba.embeddings',
        'uvicorn',
        'fastapi'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
    
    # Отключаем DEBUG логи от внешних библиотек
    external_loggers = [
        'urllib3',
        'urllib3.connectionpool',
        'sentence_transformers',
        'sentence_transformers.SentenceTransformer',
        'transformers',
        'huggingface_hub',
        'requests',
        'httpx',
        'watchfiles',  # Отключаем DEBUG логи от watchfiles
        'watchfiles.main'  # Отключаем DEBUG логи от watchfiles.main
    ]
    
    for logger_name in external_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
    
    # Отключаем DEBUG-спам от numba
    logging.getLogger('numba').setLevel(logging.WARNING)
    logging.getLogger('numba.core.byteflow').setLevel(logging.WARNING)

    logging.info("🔧 Система логирования инициализирована")
    logging.info(f"📁 Логи записываются в: {log_file}")
    
    # Отмечаем, что логирование инициализировано
    setup_logging._initialized = True

def get_logger(name: str):
    """Получает логгер с заданным именем."""
    return logging.getLogger(name)