"""
Конфигурационный файл для проекта Чатумба.
Содержит все основные настройки и параметры.
"""
import os
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

# Загружаем .env файл если он существует
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Загружен .env файл: {env_path}")
    else:
        print(f"⚠️ .env файл не найден: {env_path}")
except ImportError:
    print("⚠️ python-dotenv не установлен, переменные окружения не загружены")
except Exception as e:
    print(f"⚠️ Ошибка загрузки .env: {e}")

# Базовые пути
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = DATA_DIR / "memory"

# Создаем директории, если они не существуют
for dir_path in [DATA_DIR, MEMORY_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

# API ключи (в продакшене лучше использовать .env файл)
def get_all_openrouter_keys() -> List[str]:
    """
    Динамически собирает все доступные OpenRouter API ключи из переменных окружения.
    Поддерживает любые имена переменных, начинающиеся с OPENROUTER_API_KEY.
    Собирает ключи по номерам: OPENROUTER_API_KEY, OPENROUTER_API_KEY1, OPENROUTER_API_KEY2, и т.д.
    """
    keys = []
    
    # Сначала проверяем основной ключ
    main_key = os.environ.get("OPENROUTER_API_KEY", "")
    if main_key and main_key != "your_openrouter_api_key":
        keys.append(main_key)
    
    # Затем ищем ключи по номерам (1, 2, 3, ...)
    i = 1
    while True:
        key_name = f"OPENROUTER_API_KEY{i}"
        key_value = os.environ.get(key_name, "")
        if key_value and key_value != "your_openrouter_api_key":
            keys.append(key_value)
            i += 1
        else:
            # Если ключ не найден, прекращаем поиск
            break
    
    return keys

# Получаем все доступные ключи
OPENROUTER_API_KEYS = get_all_openrouter_keys()

# Оставляем обратную совместимость для старых переменных
OPENROUTER_API_KEY = OPENROUTER_API_KEYS[0] if OPENROUTER_API_KEYS else ""
OPENROUTER_API_KEY_2 = OPENROUTER_API_KEYS[1] if len(OPENROUTER_API_KEYS) > 1 else ""
OPENROUTER_API_KEY_3 = OPENROUTER_API_KEYS[2] if len(OPENROUTER_API_KEYS) > 2 else ""
OPENROUTER_API_KEY_4 = OPENROUTER_API_KEYS[3] if len(OPENROUTER_API_KEYS) > 3 else ""
OPENROUTER_API_KEY_5 = OPENROUTER_API_KEYS[4] if len(OPENROUTER_API_KEYS) > 4 else ""

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY", "")  # Для OpenAI embeddings

# API ключи для генерации изображений
STABLE_HORDE_API_KEY = os.environ.get("STABLE_HORDE_API_KEY", "")  # Stable Horde API ключ (ОСНОВНОЙ - БЕСПЛАТНО!)
HF_API_KEY = os.environ.get("HF_API_KEY", "")  # HuggingFace API ключ берётся только из окружения
DEEPAI_API_KEY = os.environ.get("DEEPAI_API_KEY", "")  # DeepAI API ключ (НЕ РАБОТАЕТ - ИСЧЕРПАНЫ КРЕДИТЫ)
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")  # Replicate (для справки)

# API BingX для криптотрейдинга
BINGX_API_KEY = os.environ.get("BINGX_API_KEY", "")
BINGX_SECRET_KEY = os.environ.get("BINGX_SECRET_KEY", "")
BINGX_API_URL = os.environ.get("BINGX_API_URL", "https://open-api.bingx.com")

# Настройки BingX API
BINGX_CONFIG = {
    "api_key": BINGX_API_KEY,
    "secret_key": BINGX_SECRET_KEY,
    "base_url": BINGX_API_URL,
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1,
    "testnet": os.environ.get("BINGX_TESTNET", "false").lower() == "true",
}

# Настройки LLM
LLM_CONFIG = {
    "model": "openai/gpt-oss-20b:free",  # Рабочая модель (основная)
    "fallback_model": "deepseek/deepseek-chat-v3.1:free",  # Fallback модель
    "temperature": 0.6,  # Согласно требованиям
    "max_tokens": 8000,  # Оптимальный лимит для gpt-oss-20b
    "top_p": 0.95,
}

# Cloud.ru API удален - используем только OpenRouter

# Настройки эмбеддингов
EMBEDDING_CONFIG = {
    "model": "text-embedding-3-small",  # OpenAI embedding model
    "dimensions": 384,  # Размерность для all-MiniLM-L6-v2
    "local_fallback": "all-MiniLM-L6-v2",  # HuggingFace модель для локального использования
}

# Настройки векторной базы
VECTOR_DB_CONFIG = {
    "type": "sqlite",  # faiss отключен в ассистенте
    "path": str(MEMORY_DIR / "vector_store.sqlite"),
    "collection_name": "chatumba_memory",
    "distance_metric": "cosine",
}

# Настройки SQLite
SQLITE_CONFIG = {
    "path": str(DATA_DIR / "chatumba.db"),
}

# Настройки голосовых моделей
VOICE_CONFIG = {
    "tts": {
        "model": "gtts",
        "voice": "ru_v3",
        "sample_rate": 24000,
    },
    "stt": {
        "model": "whisper",
        "language": "ru",
    }
}

# Настройки API
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 6767,
    "debug": True,
}

# Настройки Telegram бота
TELEGRAM_CONFIG = {
    "token": TELEGRAM_BOT_TOKEN,
    "webhook_url": os.environ.get("WEBHOOK_URL", ""),
    "use_webhook": False,  # True для продакшена
    "channel_id": os.environ.get("TELEGRAM_CHANNEL_ID", ""),  # ID канала для постинга
    "channel_name": os.environ.get("TELEGRAM_CHANNEL_NAME", ""),  # Имя канала (для логов)
    "enable_channel_posting": False,  # Постинг в канал отключен
}

# Базовые параметры личности Чатумбы
PERSONALITY_BASE = {
    "mood_range": {
        "happiness": (5, 10),      # Более позитивное настроение
        "energy": (3, 10),         # Больше энергии
        "irritability": (-10, 2),  # Меньше раздражительности
        "empathy": (5, 10),        # Больше эмпатии
        "reflection": (0, 8),      # Умеренная рефлексия
    },
    "reaction_weights": {
        "normal": 0.4,
        "aggressive": 0.02,        # Очень редко агрессивный
        "caring": 0.4,             # Больше заботы
        "philosophical": 0.1,
        "silent": 0.03,
        "confused": 0.05,
    },
    "memory_focus": {
        "personal": 0.4,
        "factual": 0.3,
        "emotional": 0.3,
    },
    "response_style": {
        "formality": -3,  # -10 (очень неформальный) до 10 (очень формальный)
        "verbosity": 2,   # -10 (лаконичный) до 10 (многословный)
        "humor": 7,       # -10 (серьезный) до 10 (шутливый)
        "rudeness": -5,   # -10 (вежливый) до 10 (грубый) - теперь вежливый
    }
}

# Функция для получения дневного сида на основе даты и ID пользователя
def get_daily_seed(user_id: Union[int, str]) -> int:
    """Генерирует дневной сид на основе ID пользователя и текущей даты."""
    today = datetime.datetime.now().strftime("%Y%m%d")
    seed_base = f"{user_id}_{today}"
    return hash(seed_base) % 10000  # Ограничиваем 4 цифрами для удобства

# Функция для получения базовых настроек личности с учетом дневного сида
def get_daily_personality(user_id: Union[int, str]) -> Dict:
    """Возвращает настройки личности с учетом дневного сида."""
    import random
    
    seed = get_daily_seed(user_id)
    random.seed(seed)
    
    # Копируем базовые настройки
    personality = {
        "mood": {},
        "reaction_weights": dict(PERSONALITY_BASE["reaction_weights"]),
        "memory_focus": dict(PERSONALITY_BASE["memory_focus"]),
        "response_style": dict(PERSONALITY_BASE["response_style"]),
    }
    
    # Генерируем настроение на день
    for mood, (min_val, max_val) in PERSONALITY_BASE["mood_range"].items():
        personality["mood"][mood] = random.randint(min_val, max_val)
    
    # Мутируем веса реакций (±20%)
    for key in personality["reaction_weights"]:
        mutation = random.uniform(-0.2, 0.2)
        personality["reaction_weights"][key] = max(0.01, min(0.99, 
                                                personality["reaction_weights"][key] + mutation))
    
    # Нормализуем веса, чтобы сумма была равна 1
    total = sum(personality["reaction_weights"].values())
    for key in personality["reaction_weights"]:
        personality["reaction_weights"][key] /= total
    
    # Мутируем фокус памяти (±15%)
    for key in personality["memory_focus"]:
        mutation = random.uniform(-0.15, 0.15)
        personality["memory_focus"][key] = max(0.1, min(0.9, 
                                            personality["memory_focus"][key] + mutation))
    
    # Нормализуем фокус памяти
    total = sum(personality["memory_focus"].values())
    for key in personality["memory_focus"]:
        personality["memory_focus"][key] /= total
    
    # Мутируем стиль ответов (±3 пункта)
    for key in personality["response_style"]:
        mutation = random.randint(-3, 3)
        min_val, max_val = -10, 10
        personality["response_style"][key] = max(min_val, min(max_val, 
                                              personality["response_style"][key] + mutation))
    
    return personality

class Config:
    """Централизованный класс конфигурации для приложения IKAR"""
    
    def __init__(self):
        # Основные настройки
        self.HOST = API_CONFIG["host"]
        self.PORT = API_CONFIG["port"]
        self.DEBUG = API_CONFIG["debug"]
        
        # API ключи
        self.OPENROUTER_API_KEYS = OPENROUTER_API_KEYS
        self.TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN
        self.EMBEDDING_API_KEY = EMBEDDING_API_KEY
        self.STABLE_HORDE_API_KEY = STABLE_HORDE_API_KEY
        self.HF_API_KEY = HF_API_KEY
        self.DEEPAI_API_KEY = DEEPAI_API_KEY
        self.BINGX_API_KEY = BINGX_API_KEY
        self.BINGX_SECRET_KEY = BINGX_SECRET_KEY
        
        # Конфигурации
        self.LLM_CONFIG = LLM_CONFIG
        self.EMBEDDING_CONFIG = EMBEDDING_CONFIG
        self.VECTOR_DB_CONFIG = VECTOR_DB_CONFIG
        self.SQLITE_CONFIG = SQLITE_CONFIG
        self.VOICE_CONFIG = VOICE_CONFIG
        self.TELEGRAM_CONFIG = TELEGRAM_CONFIG
        self.BINGX_CONFIG = BINGX_CONFIG
        self.PERSONALITY_BASE = PERSONALITY_BASE
        
        # Пути
        self.BASE_DIR = BASE_DIR
        self.DATA_DIR = DATA_DIR
        self.MEMORY_DIR = MEMORY_DIR
    
    def get_openrouter_key(self, index: int = 0) -> str:
        """Получить API ключ OpenRouter по индексу"""
        if 0 <= index < len(self.OPENROUTER_API_KEYS):
            return self.OPENROUTER_API_KEYS[index]
        return ""
    
    def get_daily_personality(self, user_id: Union[int, str]) -> Dict:
        """Получить дневную личность для пользователя"""
        return get_daily_personality(user_id)
    
    def get_daily_seed(self, user_id: Union[int, str]) -> int:
        """Получить дневной сид для пользователя"""
        return get_daily_seed(user_id)