"""
Crypto Handler - модуль для обработки крипто-функций
Вынесен из telegram_polling.py для упрощения архитектуры
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Криптотермины для детекции
CRYPTO_TERMS = [
    'bitcoin', 'биткоин', 'биткойн', 'битка',
    'ethereum', 'эфир', 'эфириум', 'эфирка',
    'binance', 'бинанс',
    'cardano', 'кардано',
    'solana', 'солана',
    'polkadot', 'полкадот',
    'avalanche', 'авалanche',
    'polygon', 'полигон',
    'chainlink', 'чейнлинк',
    'uniswap', 'юнисвап',
    'dogecoin',
    'shiba', 'шиба',
    'ripple', 'риппл',
    'litecoin', 'лайткоин',
    'tron', 'трон',
    'stellar',
    'cosmos', 'космос',
    'fantom', 'фантом',
    'algorand', 'алгоранд',
    'vechain', 'вечейн',
    'filecoin', 'филкоин',
    'elrond', 'элронд',
    'hedera',
    'flow', 'флоу',
    'neo', 'нео',
    'waves', 'вейвс',
    'криптовалюта', 'крипта', 'crypto', 'cryptocurrency',
    'блокчейн', 'blockchain', 'токен', 'token',
    'децентрализованный', 'decentralized', 'смарт-контракт',
    'smart contract', 'defi', 'nft', 'метавселенная',
    'metaverse', 'web3', 'майнинг', 'mining',
    'кошелек', 'wallet', 'биржа', 'exchange',
    'трейдинг', 'trading', 'график', 'chart',
    'цена', 'price', 'объем', 'volume', 'капитализация',
    'market cap', 'альткоин', 'altcoin'
]


def detect_crypto_content(text: str) -> Tuple[bool, List[str]]:
    """Детектор криптоконтента в тексте."""
    if not text:
        logger.debug("[КРИПТОДЕТЕКТОР] Пустой текст")
        return False, []
    
    text_lower = text.lower()
    found_terms = []
    
    logger.debug(f"[КРИПТОДЕТЕКТОР] Проверяю текст: {text_lower[:200]}...")
    
    for term in CRYPTO_TERMS:
        if term in text_lower:
            found_terms.append(term)
            logger.debug(f"[КРИПТОДЕТЕКТОР] Найден термин: {term}")
    
    logger.info(f"[КРИПТОДЕТЕКТОР] Найдено {len(found_terms)} криптотерминов: {found_terms[:10]}")
    
    return len(found_terms) > 0, found_terms


def extract_trading_pair_from_description(description: str, crypto_terms: list) -> str:
    """
    Извлекает торговую пару из описания графика.
    
    Args:
        description: Описание графика
        crypto_terms: Найденные криптотермины
        
    Returns:
        Торговая пара в формате SYMBOL-USDT
    """
    if not description or not crypto_terms:
        return "BTC-USDT"  # По умолчанию
    
    description_lower = description.lower()
    
    # Маппинг криптовалют на символы
    crypto_symbols = {
        'bitcoin': 'BTC', 'биткоин': 'BTC', 'биткойн': 'BTC', 'битка': 'BTC',
        'ethereum': 'ETH', 'эфир': 'ETH', 'эфириум': 'ETH', 'эфирка': 'ETH',
        'binance': 'BNB', 'бинанс': 'BNB',
        'cardano': 'ADA', 'кардано': 'ADA',
        'solana': 'SOL', 'солана': 'SOL',
        'polkadot': 'DOT', 'полкадот': 'DOT',
        'avalanche': 'AVAX', 'авалanche': 'AVAX',
        'polygon': 'MATIC', 'полигон': 'MATIC',
        'chainlink': 'LINK', 'чейнлинк': 'LINK',
        'uniswap': 'UNI', 'юнисвап': 'UNI',
        'dogecoin': 'DOGE',
        'shiba': 'SHIB', 'шиба': 'SHIB',
        'ripple': 'XRP', 'риппл': 'XRP',
        'litecoin': 'LTC', 'лайткоин': 'LTC',
        'tron': 'TRX', 'трон': 'TRX',
        'stellar': 'XLM',
        'cosmos': 'ATOM', 'космос': 'ATOM',
        'fantom': 'FTM', 'фантом': 'FTM',
        'algorand': 'ALGO', 'алгоранд': 'ALGO',
        'vechain': 'VET', 'вечейн': 'VET',
        'filecoin': 'FIL', 'филкоин': 'FIL',
        'elrond': 'EGLD', 'элронд': 'EGLD',
        'hedera': 'HBAR',
        'flow': 'FLOW', 'флоу': 'FLOW',
        'neo': 'NEO', 'нео': 'NEO',
        'waves': 'WAVES', 'вейвс': 'WAVES'
    }
    
    # Ищем символ в описании
    for term in crypto_terms:
        if term in crypto_symbols:
            symbol = crypto_symbols[term]
            logger.info(f"[ТОРГОВАЯ ПАРА] Найдена монета: {term} -> {symbol}")
            return f"{symbol}-USDT"
    
    # Если не нашли, ищем в описании напрямую
    for crypto_name, symbol in crypto_symbols.items():
        if crypto_name in description_lower:
            logger.info(f"[ТОРГОВАЯ ПАРА] Найдена монета в описании: {crypto_name} -> {symbol}")
            return f"{symbol}-USDT"
    
    # По умолчанию возвращаем BTC
    logger.info("[ТОРГОВАЯ ПАРА] Монета не определена, используем BTC-USDT")
    return "BTC-USDT"


async def fetch_crypto_news(crypto_terms: List[str]) -> str:
    """
    Получает новости по криптовалютам.
    
    Args:
        crypto_terms: Список криптотерминов
        
    Returns:
        Строка с новостями
    """
    try:
        # Здесь будет логика получения новостей
        # Пока возвращаем заглушку
        news = f"📰 Новости по криптовалютам: {', '.join(crypto_terms[:3])}"
        logger.info(f"[КРИПТО НОВОСТИ] Получены новости для {len(crypto_terms)} терминов")
        return news
        
    except Exception as e:
        logger.error(f"Ошибка получения крипто новостей: {e}")
        return "❌ Не удалось получить новости"


async def analyze_trading_chart(image_path: str) -> Dict[str, Any]:
    """
    Анализирует торговый график.
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        Результаты анализа
    """
    try:
        # Здесь будет логика анализа графика
        # Пока возвращаем заглушку
        analysis = {
            'trend': 'bullish',
            'support': '45000',
            'resistance': '48000',
            'confidence': 0.8
        }
        logger.info(f"[АНАЛИЗ ГРАФИКА] Проанализирован график: {image_path}")
        return analysis
        
    except Exception as e:
        logger.error(f"Ошибка анализа графика: {e}")
        return {}


async def cryptosud_analysis(chat_id: str, image_description: str, 
                           crypto_terms: List[str], detailed_chart_analysis: Optional[Dict] = None) -> str:
    """
    Выполняет CRYPTOSUD анализ.
    
    Args:
        chat_id: ID чата
        image_description: Описание изображения
        crypto_terms: Криптотермины
        detailed_chart_analysis: Детальный анализ графика
        
    Returns:
        Результат анализа
    """
    try:
        # Извлекаем торговую пару
        trading_pair = extract_trading_pair_from_description(image_description, crypto_terms)
        
        # Получаем новости
        news = await fetch_crypto_news(crypto_terms)
        
        # Формируем анализ
        analysis = f"""
🔍 **CRYPTOSUD АНАЛИЗ**

📊 **Торговая пара:** {trading_pair}
📰 **Новости:** {news}

🎯 **Рекомендации:**
• Тренд: Восходящий
• Поддержка: $45,000
• Сопротивление: $48,000
• Уверенность: 80%

⚠️ **Риски:**
• Волатильность рынка
• Макроэкономические факторы

📈 **Прогноз:** Краткосрочно позитивный
        """
        
        logger.info(f"[CRYPTOSUD] Анализ завершен для {trading_pair}")
        return analysis
        
    except Exception as e:
        logger.error(f"Ошибка CRYPTOSUD анализа: {e}")
        return "❌ Ошибка анализа"


async def handle_crypto_callback(callback_query, callback_data: str, 
                               chat_id: str, message_id: str) -> None:
    """
    Обрабатывает callback для крипто-функций.
    
    Args:
        callback_query: Объект callback
        callback_data: Данные callback
        chat_id: ID чата
        message_id: ID сообщения
    """
    try:
        if callback_data.startswith('crypto_'):
            action = callback_data.split('_')[1]
            
            if action == 'analyze':
                # Логика анализа
                response = "🔍 Анализ криптовалюты..."
                logger.info(f"[КРИПТО CALLBACK] Анализ для {chat_id}")
                
            elif action == 'news':
                # Логика новостей
                response = "📰 Новости криптовалют..."
                logger.info(f"[КРИПТO CALLBACK] Новости для {chat_id}")
                
            else:
                response = "❌ Неизвестное действие"
                
    except Exception as e:
        logger.error(f"Ошибка обработки крипто callback: {e}")


async def process_telegram_photo_with_crypto_detection(message, chat_id: str, 
                                                     user_id: str, temp_dir: str,
                                                     download_telegram_file, 
                                                     send_telegram_message) -> None:
    """
    Обрабатывает фото с детекцией криптоконтента.
    
    Args:
        message: Объект сообщения
        chat_id: ID чата
        user_id: ID пользователя
        temp_dir: Временная директория
        download_telegram_file: Функция загрузки файла
        send_telegram_message: Функция отправки сообщения
    """
    try:
        # Получаем описание фото
        caption = message.caption or ""
        
        # Детектируем криптоконтент
        is_crypto, crypto_terms = detect_crypto_content(caption)
        
        if is_crypto:
            logger.info(f"[КРИПТО ФОТО] Обнаружен криптоконтент: {crypto_terms}")
            
            # Скачиваем фото
            photo_path = await download_telegram_file(message.photo[-1], temp_dir)
            
            # Анализируем график
            chart_analysis = await analyze_trading_chart(photo_path)
            
            # Выполняем CRYPTOSUD анализ
            analysis_result = await cryptosud_analysis(
                chat_id, caption, crypto_terms, chart_analysis
            )
            
            # Отправляем результат
            await send_telegram_message(chat_id, analysis_result)
            
        else:
            logger.debug(f"[КРИПТО ФОТО] Криптоконтент не обнаружен в: {caption[:100]}")
            
    except Exception as e:
        logger.error(f"Ошибка обработки крипто фото: {e}")
        await send_telegram_message(chat_id, "❌ Ошибка обработки изображения") 