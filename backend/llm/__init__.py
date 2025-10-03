"""
LLM модуль - основной интерфейс для работы с языковыми моделями
"""

# Основной клиент - OpenRouter
from .openrouter import (
    OpenRouterClient,
    get_llm_client,
    init_llm_client,
)

# Для обратной совместимости
def get_openrouter_client_compat(config=None):
    """Обратная совместимость - возвращает OpenRouter клиент"""
    return get_llm_client()

# Экспортируем все основные функции
__all__ = [
    'OpenRouterClient',
    'get_llm_client',
    'init_llm_client',
    'get_openrouter_client_compat'
]