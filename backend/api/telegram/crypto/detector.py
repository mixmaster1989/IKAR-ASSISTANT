"""
Модуль для детекции криптоконтента в тексте.
Отвечает за определение криптотерминов и извлечение торговых пар.
"""
import logging
from typing import Tuple, List

logger = logging.getLogger("chatumba.crypto.detector")

# Криптотермины для детекции
CRYPTO_TERMS = [
    # Основные криптовалюты
    'bitcoin', 'btc', 'биткоин', 'биткойн', 'битка',
    'ethereum', 'eth', 'эфир', 'эфириум', 'эфирка',
    'binance', 'bnb', 'бинанс',
    'cardano', 'ada', 'кардано',
    'solana', 'sol', 'солана',
    'polkadot', 'dot', 'полкадот',
    'avalanche', 'avax', 'авалanche',
    'polygon', 'matic', 'полигон',
    'chainlink', 'link', 'чейнлинк',
    'uniswap', 'uni', 'юнисвап',
    'dogecoin', 'doge', 'догекоин',
    'shiba', 'shib', 'шиба',
    'ripple', 'xrp', 'риппл',
    'litecoin', 'ltc', 'лайткоин',
    'tron', 'trx', 'трон',
    'stellar', 'xlm',
    'cosmos', 'atom', 'космос',
    'fantom', 'ftm', 'фантом',
    'algorand', 'algo', 'алгоранд',
    'vechain', 'vet', 'вечейн',
    'filecoin', 'fil', 'филкоин',
    'elrond', 'egld', 'элронд',
    'hedera', 'hbar',
    'flow', 'флоу',
    'neo', 'нео',
    'waves', 'wav', 'вейвс',
    'pepe', 'пепе',
    'usdt', 'tether', 'тетер',
    
    # Торговые термины
    'long', 'лонг', 'short', 'шорт', 'позиция',
    'leverage', 'рычаг', 'leverage', 'леверидж',
    'margin', 'маржа', 'маржинальная торговля',
    'futures', 'фьючерсы', 'фьючерс',
    'spot', 'спот', 'спотовая торговля',
    'order', 'ордер', 'заявка', 'ордер',
    'buy', 'покупка', 'buy', 'бай',
    'sell', 'продажа', 'sell', 'селл',
    'stop loss', 'стоп лосс', 'стоплосс',
    'take profit', 'тейк профит', 'тейкпрофит',
    'support', 'поддержка', 'support',
    'resistance', 'сопротивление', 'resistance',
    'trend', 'тренд', 'тренд',
    'breakout', 'пробой', 'breakout',
    'breakdown', 'пробой вниз', 'breakdown',
    'consolidation', 'консолидация', 'consolidation',
    'volatility', 'волатильность', 'волатил',
    'volume', 'объем', 'volume',
    'market cap', 'капитализация', 'маркет кап',
    'dominance', 'доминация', 'dominance',
    
    # Аналитические термины
    'technical analysis', 'технический анализ', 'тех анализ',
    'fundamental analysis', 'фундаментальный анализ',
    'chart', 'график', 'чарт',
    'candlestick', 'свеча', 'candlestick',
    'moving average', 'скользящая средняя', 'ма',
    'rsi', 'relative strength index',
    'macd', 'moving average convergence divergence',
    'bollinger bands', 'полосы боллинджера',
    'fibonacci', 'фибоначчи', 'фиб',
    'elliot wave', 'волны эллиота',
    'head and shoulders', 'голова и плечи',
    'double top', 'двойная вершина',
    'double bottom', 'двойное дно',
    'triangle', 'треугольник', 'triangle',
    'flag', 'флаг', 'flag',
    'pennant', 'вымпел', 'pennant',
    
    # Платформы и биржи
    'binance', 'бинанс', 'binance',
    'coinbase', 'коинбейс', 'coinbase',
    'kraken', 'кракен', 'kraken',
    'kucoin', 'кукоин', 'kucoin',
    'okx', 'окх', 'okx',
    'bybit', 'байбит', 'bybit',
    'bingx', 'бингкс', 'bingx',
    'huobi', 'хуоби', 'huobi',
    'gate.io', 'гейт', 'gate',
    'mexc', 'мекс', 'mexc',
    'bitget', 'битгет', 'bitget',
    
    # Децентрализованные платформы
    'uniswap', 'юнисвап', 'uniswap',
    'pancakeswap', 'панкейксвап', 'pancakeswap',
    'sushiswap', 'сушисвап', 'sushiswap',
    'curve', 'кривая', 'curve',
    'aave', 'аав', 'aave',
    'compound', 'компаунд', 'compound',
    'makerdao', 'мейкердао', 'makerdao',
    'yearn finance', 'йирн файнэнс', 'yearn',
    
    # Торговые стратегии
    'scalping', 'скальпинг', 'scalping',
    'day trading', 'дневная торговля', 'дей трейдинг',
    'swing trading', 'свинг трейдинг', 'свинг',
    'position trading', 'позиционная торговля',
    'grid trading', 'сеточная торговля', 'грид',
    'dca', 'dollar cost averaging', 'усреднение',
    'hodl', 'холд', 'hodl',
    'fomo', 'страх упустить', 'fomo',
    'fud', 'страх, неуверенность, сомнение', 'fud',
    'moon', 'луна', 'moon',
    'lambo', 'ламбо', 'lambo',
    'rekt', 'рект', 'rekt',
    'wagmi', 'we all gonna make it', 'wagmi',
    'ngmi', 'not gonna make it', 'ngmi',
    
    # Риск-менеджмент
    'risk management', 'управление рисками', 'риск менеджмент',
    'portfolio', 'портфель', 'портфолио',
    'diversification', 'диверсификация', 'diversification',
    'allocation', 'аллокация', 'allocation',
    'hedging', 'хеджирование', 'хедж', 'hedge',
    
    # Рыночные термины
    'bull', 'бык', 'бычий', 'bullish',
    'bear', 'медведь', 'медвежий', 'bearish',
    'sideways', 'флет', 'боковик', 'sideways',
    'pump', 'памп', 'pump',
    'dump', 'дамп', 'dump',
    'pump and dump', 'памп и дамп', 'pump and dump',
    'whales', 'киты', 'whale', 'кит',
    'retail', 'ретейл', 'retail',
    'institutional', 'институциональный', 'institutional',
    'funds', 'фонды', 'funds',
    
    # Дополнительные термины
    'cryptocurrency', 'криптовалюта', 'крипта', 'crypto',
    'blockchain', 'блокчейн', 'blockchain',
    'mining', 'майнинг', 'mining', 'майнер',
    'hash', 'хеш', 'hash',
    'hashrate', 'хешрейт', 'hashrate',
    'nodes', 'ноды', 'nodes',
    'wallet', 'кошелек', 'валлет', 'wallet',
    'seed', 'сид', 'seed',
    'private key', 'приватный ключ', 'private key',
    'public key', 'публичный ключ', 'public key',
    'address', 'адрес', 'address',
    'transaction', 'транзакция', 'тх', 'tx',
    'fee', 'комиссия', 'fee',
    'gas', 'газ', 'gas',
    'gwei', 'гвей', 'gwei',
    'satoshi', 'сатоши', 'сат', 'satoshi',
    'wei', 'вей', 'wei',
    'finney', 'финни', 'finney',
    'ether', 'эфир', 'ether',
    'defi', 'дефи', 'defi',
    'nft', 'нфт', 'nft',
    'dao', 'дао', 'dao',
    'dex', 'декс', 'dex',
    'cex', 'цекс', 'cex',
    'amm', 'амм', 'amm',
    'yield', 'йилд', 'yield',
    'farming', 'фарминг', 'farming',
    'staking', 'стейкинг', 'staking',
    'liquidity mining', 'ликвидити майнинг', 'liquidity mining',
    'airdrop', 'аирдроп', 'дроп', 'airdrop',
    'ido', 'идо', 'ido',
    'ico', 'ико', 'ico',
    'ieo', 'иео', 'ieo',
    'launchpad', 'лончпад', 'launchpad',
    'whitelist', 'вайтлист', 'whitelist',
    'kyc', 'кус', 'kyc',
    'tradingview', 'трейдингвью', 'тв', 'tv',
    'coingecko', 'коингеко', 'coingecko',
    'coinmarketcap', 'кмс', 'cmc', 'coinmarketcap'
]

def detect_crypto_content(text: str) -> Tuple[bool, List[str]]:
    """
    Детектор криптоконтента в тексте.
    
    Args:
        text: Текст для анализа
        
    Returns:
        Tuple[bool, List[str]]: (найден_криптоконтент, список_найденных_терминов)
    """
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
    'waves': 'WAVES', 'вейвс': 'WAVES',
    'pepe': 'PEPE', 'пепе': 'PEPE',
    'usdt': 'USDT', 'tether': 'USDT'
}

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

