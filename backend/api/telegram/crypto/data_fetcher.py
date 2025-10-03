"""
Модуль для получения крипто-данных из различных источников.
Отвечает за сбор данных с BingX, CoinGecko, Binance и других API.
"""
import logging
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("chatumba.crypto.data_fetcher")

# Безопасный импорт BingX интеграции
from utils.import_helper import get_bingx_client, get_crypto_integration


async def fetch_bingx_market_data(trading_pair: str) -> dict:
    """
    Получает рыночные данные с BingX.
    
    Args:
        trading_pair: Торговая пара (например, BTC-USDT)
        
    Returns:
        Словарь с рыночными данными
    """
    try:
        bingx_client = get_bingx_client()
        if not bingx_client:
            return {"error": "BingX клиент недоступен"}
        
        # Получаем различные типы данных
        ticker = bingx_client.get_ticker_24hr(trading_pair)
        order_book = bingx_client.get_order_book(trading_pair, limit=50)
        recent_trades = bingx_client.get_recent_trades(trading_pair, limit=100)
        klines_1h = bingx_client.get_klines(trading_pair, interval='1h', limit=24)
        klines_4h = bingx_client.get_klines(trading_pair, interval='4h', limit=30)
        
        # Анализируем настроения
        sentiment = bingx_client.analyze_market_sentiment(trading_pair, '1h')
        
        market_data = {
            'symbol': trading_pair,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'ticker': ticker,
            'order_book': order_book,
            'recent_trades': recent_trades,
            'klines_1h': klines_1h,
            'klines_4h': klines_4h,
            'sentiment': sentiment
        }
        
        logger.info(f"[BINGX] Получены данные для {trading_pair}")
        return market_data
        
    except Exception as e:
        logger.error(f"[BINGX] Ошибка получения данных: {e}")
        return {"error": str(e)}


def format_bingx_data_for_prompts(bingx_data: dict) -> str:
    """
    Форматирует данные BingX для промптов.
    """
    if not bingx_data or "error" in bingx_data:
        return "❌ Данные BingX недоступны"
    
    formatted = f"📊 **ДАННЫЕ BINGX:**\n\n"
    
    # Тикер
    if "ticker" in bingx_data and bingx_data["ticker"]:
        ticker_data = bingx_data["ticker"].get("data", {})
        if ticker_data and isinstance(ticker_data, dict):
            formatted += f"💰 **ТИКЕР:**\n"
            formatted += f"• Цена: ${ticker_data.get('lastPrice', 'N/A')}\n"
            formatted += f"• Изменение 24ч: {ticker_data.get('priceChangePercent', 'N/A')}%\n"
            formatted += f"• Объем 24ч: {ticker_data.get('volume', 'N/A')}\n"
            formatted += f"• Максимум 24ч: ${ticker_data.get('highPrice', 'N/A')}\n"
            formatted += f"• Минимум 24ч: ${ticker_data.get('lowPrice', 'N/A')}\n\n"
    
    # Стакан заявок
    if "order_book" in bingx_data and bingx_data["order_book"]:
        order_book_data = bingx_data["order_book"].get("data", {})
        if order_book_data and isinstance(order_book_data, dict):
            bids = order_book_data.get("bids", [])
            asks = order_book_data.get("asks", [])
            
            formatted += f"📋 **СТАКАН ЗАЯВОК:**\n"
            if bids:
                formatted += f"• Лучшая покупка: ${bids[0][0]} ({bids[0][1]})\n"
            if asks:
                formatted += f"• Лучшая продажа: ${asks[0][0]} ({asks[0][1]})\n"
            
            # Глубина рынка
            bid_depth = sum(float(bid[1]) for bid in bids[:5]) if bids else 0
            ask_depth = sum(float(ask[1]) for ask in asks[:5]) if asks else 0
            formatted += f"• Глубина покупок (топ-5): {bid_depth:.2f}\n"
            formatted += f"• Глубина продаж (топ-5): {ask_depth:.2f}\n\n"
    
    # Последние сделки
    if "recent_trades" in bingx_data and bingx_data["recent_trades"]:
        trades_data = bingx_data["recent_trades"].get("data", [])
        if trades_data and isinstance(trades_data, list) and len(trades_data) > 0:
            formatted += f"🔄 **ПОСЛЕДНИЕ СДЕЛКИ:**\n"
            # Показываем последние 5 сделок
            for i, trade in enumerate(trades_data[:5]):
                price = trade.get("price", "N/A")
                qty = trade.get("qty", "N/A")
                side = "🟢" if trade.get("isBuyerMaker") else "🔴"
                formatted += f"• {side} ${price} ({qty})\n"
            formatted += "\n"
    
    # Анализ настроений
    if "sentiment" in bingx_data and bingx_data["sentiment"]:
        sentiment_data = bingx_data["sentiment"]
        formatted += f"🎭 **АНАЛИЗ НАСТРОЕНИЙ:**\n"
        formatted += f"• Настроение: {sentiment_data.get('sentiment', 'N/A')}\n"
        formatted += f"• Сила сигнала: {sentiment_data.get('strength', 'N/A')}\n\n"
    
    # Комплексный анализ
    if "comprehensive_analysis" in bingx_data and bingx_data["comprehensive_analysis"]:
        comp_data = bingx_data["comprehensive_analysis"]
        if "analysis" in comp_data:
            analysis = comp_data["analysis"]
            formatted += f"🔍 **КОМПЛЕКСНЫЙ АНАЛИЗ:**\n"
            formatted += f"• Ликвидность: {analysis.get('liquidity_score', 'N/A')}\n"
            formatted += f"• Волатильность: {analysis.get('volatility_score', 'N/A')}%\n"
            formatted += f"• Сила тренда: {analysis.get('trend_strength', 'N/A')}\n"
            
            # Уровни поддержки/сопротивления
            support_resistance = analysis.get("support_resistance", {})
            if support_resistance:
                formatted += f"• Ближайшая поддержка: ${support_resistance.get('nearest_support', 'N/A')}\n"
                formatted += f"• Ближайшее сопротивление: ${support_resistance.get('nearest_resistance', 'N/A')}\n"
            formatted += "\n"
    
    formatted += f"⏰ Время получения: {bingx_data.get('timestamp', 'N/A')}\n"
    formatted += f"📡 Источник: {' + '.join(bingx_data.get('data_sources', ['BingX API']))}\n"
    
    return formatted


async def fetch_ultimate_crypto_data(crypto_terms: List[str]) -> str:
    """
    Максимальный сбор данных о криптовалюте из множественных источников.
    
    Args:
        crypto_terms: Список криптотерминов
        
    Returns:
        Строка с агрегированными данными
    """
    logger.info(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Начинаю максимальный сбор данных для: {crypto_terms[:3]}")
    
    ultimate_data = []
    
    # Определяем основную монету из терминов
    main_coin = None
    coin_mapping = {
        'bitcoin': 'bitcoin', 'btc': 'bitcoin',
        'ethereum': 'ethereum', 'eth': 'ethereum', 
        'pepe': 'pepe', 'пепе': 'pepe',
        'usdt': 'tether', 'tether': 'tether',
        'bnb': 'binancecoin', 'binance': 'binancecoin'
    }
    
    for term in crypto_terms:
        if term.lower() in coin_mapping:
            main_coin = coin_mapping[term.lower()]
            break
    
    if not main_coin:
        main_coin = 'bitcoin'  # Fallback
    
    logger.info(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Основная монета для анализа: {main_coin}")
    
    async with aiohttp.ClientSession() as session:
        
        # 1. ДЕТАЛЬНЫЕ ДАННЫЕ COINGECKO
        try:
            logger.info("[УЛЬТИМЕЙТ-ДАННЫЕ] Запрашиваю детальные данные CoinGecko...")
            url = f'https://api.coingecko.com/api/v3/coins/{main_coin}'
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    market_data = data.get('market_data', {})
                    
                    current_price = market_data.get('current_price', {}).get('usd', 0)
                    price_change_24h = market_data.get('price_change_percentage_24h', 0)
                    price_change_7d = market_data.get('price_change_percentage_7d', 0)
                    market_cap = market_data.get('market_cap', {}).get('usd', 0)
                    volume_24h = market_data.get('total_volume', {}).get('usd', 0)
                    
                    ultimate_data.append(f"💰 {data.get('name', 'Unknown')} (${current_price:.6f})")
                    ultimate_data.append(f"📊 24h: {price_change_24h:.2f}% | 7d: {price_change_7d:.2f}%")
                    ultimate_data.append(f"💎 Market Cap: ${market_cap:,.0f}")
                    ultimate_data.append(f"📈 Volume 24h: ${volume_24h:,.0f}")
                    
                    logger.info(f"[УЛЬТИМЕЙТ-ДАННЫЕ] CoinGecko: {current_price} USD, {price_change_24h:.2f}%")
        except Exception as e:
            logger.error(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Ошибка CoinGecko: {e}")
        
        # 2. FEAR & GREED INDEX
        try:
            logger.info("[УЛЬТИМЕЙТ-ДАННЫЕ] Запрашиваю Fear & Greed Index...")
            async with session.get('https://api.alternative.me/fng/', timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    fng_data = data.get('data', [{}])[0]
                    fng_value = fng_data.get('value', 'N/A')
                    fng_classification = fng_data.get('value_classification', 'Unknown')
                    
                    ultimate_data.append(f"😱 Fear & Greed: {fng_value} ({fng_classification})")
                    logger.info(f"[УЛЬТИМЕЙТ-ДАННЫЕ] F&G Index: {fng_value} - {fng_classification}")
        except Exception as e:
            logger.error(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Ошибка F&G Index: {e}")
        
        # 3. BINANCE TICKER DATA
        try:
            logger.info("[УЛЬТИМЕЙТ-ДАННЫЕ] Запрашиваю данные Binance...")
            symbol = f"{main_coin.upper()}USDT" if main_coin != 'tether' else 'BTCUSDT'
            if main_coin == 'pepe':
                symbol = 'PEPEUSDT'
            elif main_coin == 'ethereum':
                symbol = 'ETHUSDT'
            
            url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    price = float(data.get('lastPrice', 0))
                    change_percent = float(data.get('priceChangePercent', 0))
                    volume = float(data.get('volume', 0))
                    high_24h = float(data.get('highPrice', 0))
                    low_24h = float(data.get('lowPrice', 0))
                    
                    ultimate_data.append(f"🔥 Binance: ${price:.6f} ({change_percent:+.2f}%)")
                    ultimate_data.append(f"📊 24h High: ${high_24h:.6f} | Low: ${low_24h:.6f}")
                    ultimate_data.append(f"💹 Volume: {volume:,.0f}")
                    
                    logger.info(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Binance: {price} USD, {change_percent}%")
        except Exception as e:
            logger.error(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Ошибка Binance: {e}")
    
    if not ultimate_data:
        ultimate_data = ["📊 Не удалось получить расширенные данные"]
        logger.warning("[УЛЬТИМЕЙТ-ДАННЫЕ] Не получено данных, используем fallback")
    
    result = "\n".join(ultimate_data)
    logger.info(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Собрано {len(ultimate_data)} строк данных")
    return result


async def fetch_macro_economic_data() -> str:
    """
    Получение актуальных макроэкономических данных.
    
    Returns:
        Строка с макроэкономическими данными
    """
    logger.info("[МАКРОДАННЫЕ] Начинаю сбор макроэкономических данных...")
    
    macro_data = []
    current_date = datetime.now().strftime("%d.%m.%Y")
    current_year = datetime.now().year
    
    macro_data.append(f"📅 ТЕКУЩАЯ ДАТА: {current_date} ({current_year} год)")
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Fear & Greed Index
        try:
            logger.info("[МАКРОДАННЫЕ] Запрашиваю Fear & Greed Index...")
            async with session.get('https://api.alternative.me/fng/', timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    fng_data = data.get('data', [{}])[0]
                    fng_value = fng_data.get('value', 'N/A')
                    fng_classification = fng_data.get('value_classification', 'Unknown')
                    fng_date = fng_data.get('timestamp', '')
                    
                    macro_data.append(f"😱 Fear & Greed Index: {fng_value}/100 ({fng_classification})")
                    if fng_date:
                        fng_readable = datetime.fromtimestamp(int(fng_date)).strftime('%d.%m.%Y')
                        macro_data.append(f"📊 Обновлено: {fng_readable}")
        except Exception as e:
            logger.error(f"[МАКРОДАННЫЕ] Ошибка F&G Index: {e}")
        
        # 2. Bitcoin данные
        try:
            logger.info("[МАКРОДАННЫЕ] Запрашиваю данные Bitcoin...")
            async with session.get('https://api.coingecko.com/api/v3/coins/bitcoin', timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    market_data = data.get('market_data', {})
                    
                    current_price = market_data.get('current_price', {}).get('usd', 0)
                    ath_price = market_data.get('ath', {}).get('usd', 0)
                    ath_date = market_data.get('ath_date', {}).get('usd', '')
                    
                    if ath_price > 0:
                        ath_distance = ((current_price - ath_price) / ath_price) * 100
                        macro_data.append(f"🏔️ Bitcoin ATH: ${ath_price:,.0f} ({ath_distance:+.1f}% от ATH)")
                    
                    if ath_date:
                        ath_readable = datetime.fromisoformat(ath_date.replace('Z', '+00:00')).strftime('%d.%m.%Y')
                        macro_data.append(f"📈 ATH достигнут: {ath_readable}")
                    
                    # Анализ халвинга
                    last_halving = datetime(2024, 4, 20)
                    next_halving = datetime(2028, 4, 20)
                    days_since_halving = (datetime.now() - last_halving).days
                    days_to_halving = (next_halving - datetime.now()).days
                    
                    macro_data.append(f"⚡ Дней с халвинга 2024: {days_since_halving}")
                    macro_data.append(f"⏳ Дней до халвинга 2028: {days_to_halving}")
                    
        except Exception as e:
            logger.error(f"[МАКРОДАННЫЕ] Ошибка Bitcoin данных: {e}")
        
        # 3. Глобальные данные
        try:
            logger.info("[МАКРОДАННЫЕ] Запрашиваю глобальные рыночные данные...")
            async with session.get('https://api.coingecko.com/api/v3/global', timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    global_data = data.get('data', {})
                    
                    total_market_cap = global_data.get('total_market_cap', {}).get('usd', 0)
                    btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
                    eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
                    active_cryptos = global_data.get('active_cryptocurrencies', 0)
                    
                    macro_data.append(f"🌍 Общая капитализация крипторынка: ${total_market_cap:,.0f}")
                    macro_data.append(f"👑 Доминация BTC: {btc_dominance:.1f}% | ETH: {eth_dominance:.1f}%")
                    macro_data.append(f"🪙 Активных криптовалют: {active_cryptos:,}")
                    
                    # Анализ доминации
                    if btc_dominance > 50:
                        macro_data.append(f"📊 Фаза рынка: Bitcoin Season (доминация {btc_dominance:.1f}%)")
                    elif btc_dominance < 40:
                        macro_data.append(f"🚀 Фаза рынка: Alt Season (доминация BTC {btc_dominance:.1f}%)")
                    else:
                        macro_data.append(f"⚖️ Фаза рынка: Переходная (доминация BTC {btc_dominance:.1f}%)")
        except Exception as e:
            logger.error(f"[МАКРОДАННЫЕ] Ошибка глобальных данных: {e}")
        
        # 4. Институциональные данные
        try:
            logger.info("[МАКРОДАННЫЕ] Анализирую институциональную активность...")
            macro_data.append(f"🏛️ Институциональный контекст {current_year}:")
            macro_data.append(f"• Bitcoin ETF одобрены в США (январь 2024)")
            macro_data.append(f"• Ethereum ETF одобрены в США (июль 2024)")
            macro_data.append(f"• MicroStrategy продолжает накопление BTC")
            macro_data.append(f"• Растущее принятие корпорациями")
        except Exception as e:
            logger.error(f"[МАКРОДАННЫЕ] Ошибка институциональных данных: {e}")
    
    if not macro_data:
        macro_data = [f"📊 Макроэкономические данные временно недоступны ({current_date})"]
    
    result = "\n".join(macro_data)
    logger.info(f"[МАКРОДАННЫЕ] Собрано {len(macro_data)} строк макроданных")
    return result


async def fetch_crypto_news(crypto_terms: List[str]) -> str:
    """
    Получает новости по криптовалютам.
    
    Args:
        crypto_terms: Список криптотерминов
        
    Returns:
        Строка с новостями
    """
    logger.info(f"[КРИПТОНОВОСТИ] Начинаю парсинг для терминов: {crypto_terms[:5]}")
    
    try:
        news_data = []
        
        async with aiohttp.ClientSession() as session:
            # CoinGecko trending
            try:
                logger.info("[КРИПТОНОВОСТИ] Запрашиваю трендовые монеты с CoinGecko...")
                async with session.get('https://api.coingecko.com/api/v3/search/trending', timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        trending = data.get('coins', [])
                        logger.info(f"[КРИПТОНОВОСТИ] Получено {len(trending)} трендовых монет")
                        for coin in trending[:5]:
                            coin_data = coin.get('item', {})
                            coin_name = coin_data.get('name', 'Unknown')
                            coin_symbol = coin_data.get('symbol', 'N/A')
                            news_data.append(f"📈 Trending: {coin_name} ({coin_symbol})")
            except Exception as e:
                logger.error(f"[КРИПТОНОВОСТИ] Ошибка при запросе трендовых монет: {e}")
            
            # Глобальные данные
            try:
                logger.info("[КРИПТОНОВОСТИ] Запрашиваю глобальные данные рынка...")
                async with session.get('https://api.coingecko.com/api/v3/global', timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        global_data = data.get('data', {})
                        market_cap = global_data.get('total_market_cap', {}).get('usd', 0)
                        btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
                        news_data.append(f"💰 Общая капитализация: ${market_cap:,.0f}")
                        news_data.append(f"₿ Доминация Bitcoin: {btc_dominance:.1f}%")
            except Exception as e:
                logger.error(f"[КРИПТОНОВОСТИ] Ошибка при запросе глобальных данных: {e}")
        
        if not news_data:
            news_data = ["📊 Актуальные данные временно недоступны"]
        
        result = "\n".join(news_data)
        logger.info(f"[КРИПТОНОВОСТИ] Итоговые данные ({len(news_data)} строк)")
        return result
        
    except Exception as e:
        logger.error(f"[КРИПТОНОВОСТИ] Общая ошибка: {e}")
        return "📊 Новости временно недоступны"


async def validate_price_from_apis(trading_pair: str, chart_price: float) -> tuple:
    """
    Валидация цены с графика через реальные API.
    
    Args:
        trading_pair: Торговая пара
        chart_price: Цена с графика
        
    Returns:
        Tuple[float, List]: (валидированная_цена, список_источников)
    """
    logger.info(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Проверяю цену {chart_price} для пары {trading_pair}")
    
    validated_prices = []
    
    # Определяем символ для разных API
    pair_mapping = {
        'PEPE/USDT': {'binance': 'PEPEUSDT', 'coingecko': 'pepe'},
        'BTC/USDT': {'binance': 'BTCUSDT', 'coingecko': 'bitcoin'},
        'ETH/USDT': {'binance': 'ETHUSDT', 'coingecko': 'ethereum'},
        'BNB/USDT': {'binance': 'BNBUSDT', 'coingecko': 'binancecoin'}
    }
    
    pair_info = pair_mapping.get(trading_pair.upper())
    if not pair_info:
        logger.warning(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Неизвестная пара: {trading_pair}")
        return chart_price, []
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Binance API
        try:
            binance_symbol = pair_info['binance']
            url = f'https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}'
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    binance_price = float(data.get('price', 0))
                    validated_prices.append(('Binance', binance_price))
                    logger.info(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Binance: {binance_price}")
        except Exception as e:
            logger.error(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Ошибка Binance: {e}")
        
        # 2. CoinGecko API
        try:
            coingecko_id = pair_info['coingecko']
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={coingecko_id}&vs_currencies=usd'
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    coingecko_price = data.get(coingecko_id, {}).get('usd', 0)
                    if coingecko_price:
                        validated_prices.append(('CoinGecko', coingecko_price))
                        logger.info(f"[ВАЛИДАЦИЯ-ЦЕНЫ] CoinGecko: {coingecko_price}")
        except Exception as e:
            logger.error(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Ошибка CoinGecko: {e}")
    
    # Анализируем валидацию
    if validated_prices:
        avg_price = sum(price for _, price in validated_prices) / len(validated_prices)
        
        # Проверяем отклонение цены с графика
        if chart_price and chart_price > 0:
            deviation = abs(chart_price - avg_price) / avg_price * 100
            logger.info(f"[ВАЛИДАЦИЯ-ЦЕНЫ] График: {chart_price}, Среднее API: {avg_price:.8f}, Отклонение: {deviation:.1f}%")
            
            if deviation > 10:  # Если отклонение больше 10%
                logger.warning(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Большое отклонение! Используем цену из API")
                return avg_price, validated_prices
        
        return chart_price or avg_price, validated_prices
    
    return chart_price, []

