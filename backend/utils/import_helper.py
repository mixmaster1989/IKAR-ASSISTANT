"""
Вспомогательный модуль для надежных импортов.
Решает проблемы с относительными импортами в разных контекстах выполнения.
"""

import sys
import importlib
from pathlib import Path
from typing import Any, Optional


def safe_import(module_path: str, fallback_path: str = None) -> Optional[Any]:
    """
    Безопасно импортирует модуль, пытаясь разные пути импорта.
    
    Args:
        module_path: Путь к модулю (например, 'api.bingx_api')
        fallback_path: Альтернативный путь для импорта
        
    Returns:
        Импортированный модуль или None
    """
    try:
        # Пытаемся импортировать как есть
        return importlib.import_module(module_path)
    except ImportError:
        try:
            # Добавляем путь к backend в sys.path
            backend_path = Path(__file__).parent.parent
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))
            
            # Пытаемся импортировать снова
            return importlib.import_module(module_path)
        except ImportError:
            if fallback_path:
                try:
                    # Пытаемся альтернативный путь
                    return importlib.import_module(fallback_path)
                except ImportError:
                    pass
            return None


def get_crypto_integration():
    """
    Безопасно получает экземпляр crypto_integration.
    
    Returns:
        Экземпляр CryptoExchangeIntegration или None
    """
    try:
        # Пытаемся импортировать через разные пути
        crypto_module = safe_import('api.crypto_exchange_integration')
        if crypto_module:
            return crypto_module.crypto_integration
        
        # Альтернативный путь
        crypto_module = safe_import('crypto_exchange_integration')
        if crypto_module:
            return crypto_module.crypto_integration
            
    except Exception:
        pass
    
    return None


def get_bingx_client():
    """
    Безопасно получает экземпляр bingx_client.
    
    Returns:
        Экземпляр BingXAPI или None
    """
    try:
        # Пытаемся импортировать через разные пути
        bingx_module = safe_import('api.bingx_api')
        if bingx_module:
            return bingx_module.bingx_client
        
        # Альтернативный путь
        bingx_module = safe_import('bingx_api')
        if bingx_module:
            return bingx_module.bingx_client
            
    except Exception:
        pass
    
    return None


 