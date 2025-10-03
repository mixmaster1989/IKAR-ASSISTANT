"""
Пакет для крипто-функций Telegram бота.
Модульная архитектура на основе SOLID принципов.
"""

# Экспорт из detector.py
from .detector import (
    detect_crypto_content,
    extract_trading_pair_from_description,
    CRYPTO_TERMS,
    crypto_symbols
)

# Экспорт из data_fetcher.py
from .data_fetcher import (
    fetch_bingx_market_data,
    fetch_ultimate_crypto_data,
    fetch_macro_economic_data,
    fetch_crypto_news,
    format_bingx_data_for_prompts,
    validate_price_from_apis
)

# Экспорт из analyzer.py
from .analyzer import (
    analyze_trading_chart
)

# Экспорт из cryptosud.py
from .cryptosud import (
    cryptosud_analysis
)

# Экспорт из telegram_handler.py
from .telegram_handler import (
    handle_crypto_callback,
    process_telegram_photo_with_crypto_detection
)

__all__ = [
    # Detector
    'detect_crypto_content',
    'extract_trading_pair_from_description',
    'CRYPTO_TERMS',
    'crypto_symbols',
    
    # Data Fetcher
    'fetch_bingx_market_data',
    'fetch_ultimate_crypto_data',
    'fetch_macro_economic_data',
    'fetch_crypto_news',
    'format_bingx_data_for_prompts',
    'validate_price_from_apis',
    
    # Analyzer
    'analyze_trading_chart',
    
    # Cryptosud
    'cryptosud_analysis',
    'CryptoSudAnalyzer',
    'cryptosud_analyzer',
    
    # Telegram Handler
    'handle_crypto_callback',
    'process_telegram_photo_with_crypto_detection'
]
