import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем функцию сбора максимальных данных о криптовалюте
ultimate_data_function = '''
async def fetch_ultimate_crypto_data(crypto_terms):
    """Максимальный сбор данных о криптовалюте из множественных источников."""
    import aiohttp
    import json
    
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
        
        # 3. BINANCE TICKER DATA (без авторизации)
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
        
        # 4. COINPAPRIKA API (открытый)
        try:
            logger.info("[УЛЬТИМЕЙТ-ДАННЫЕ] Запрашиваю данные CoinPaprika...")
            # Маппинг для CoinPaprika ID
            paprika_mapping = {
                'bitcoin': 'btc-bitcoin',
                'ethereum': 'eth-ethereum',
                'pepe': 'pepe-pepe',
                'tether': 'usdt-tether'
            }
            
            paprika_id = paprika_mapping.get(main_coin, 'btc-bitcoin')
            url = f'https://api.coinpaprika.com/v1/tickers/{paprika_id}'
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    quotes = data.get('quotes', {}).get('USD', {})
                    
                    price = quotes.get('price', 0)
                    change_1h = quotes.get('percent_change_1h', 0)
                    change_24h = quotes.get('percent_change_24h', 0)
                    ath_price = quotes.get('ath_price', 0)
                    
                    ultimate_data.append(f"📈 CoinPaprika: ${price:.6f}")
                    ultimate_data.append(f"⏰ 1h: {change_1h:+.2f}% | 24h: {change_24h:+.2f}%")
                    if ath_price > 0:
                        ath_distance = ((price - ath_price) / ath_price) * 100
                        ultimate_data.append(f"🏔️ ATH: ${ath_price:.6f} ({ath_distance:+.1f}%)")
                    
                    logger.info(f"[УЛЬТИМЕЙТ-ДАННЫЕ] CoinPaprika: {price} USD")
        except Exception as e:
            logger.error(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Ошибка CoinPaprika: {e}")
        
        # 5. CRYPTO COMPARE (открытый API)
        try:
            logger.info("[УЛЬТИМЕЙТ-ДАННЫЕ] Запрашиваю данные CryptoCompare...")
            symbol_map = {
                'bitcoin': 'BTC',
                'ethereum': 'ETH', 
                'pepe': 'PEPE',
                'tether': 'USDT'
            }
            
            symbol = symbol_map.get(main_coin, 'BTC')
            url = f'https://min-api.cryptocompare.com/data/pricemultifull?fsyms={symbol}&tsyms=USD'
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    raw_data = data.get('RAW', {}).get(symbol, {}).get('USD', {})
                    
                    price = raw_data.get('PRICE', 0)
                    change_24h = raw_data.get('CHANGEPCT24HOUR', 0)
                    volume_24h = raw_data.get('VOLUME24HOUR', 0)
                    supply = raw_data.get('SUPPLY', 0)
                    
                    ultimate_data.append(f"💎 CryptoCompare: ${price:.6f}")
                    ultimate_data.append(f"📊 Change 24h: {change_24h:+.2f}%")
                    ultimate_data.append(f"🔄 Supply: {supply:,.0f}")
                    
                    logger.info(f"[УЛЬТИМЕЙТ-ДАННЫЕ] CryptoCompare: {price} USD")
        except Exception as e:
            logger.error(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Ошибка CryptoCompare: {e}")
        
        # 6. ДОПОЛНИТЕЛЬНЫЕ РЫНОЧНЫЕ ДАННЫЕ
        try:
            logger.info("[УЛЬТИМЕЙТ-ДАННЫЕ] Запрашиваю дополнительные рыночные данные...")
            
            # Bitcoin dominance и общий рынок
            async with session.get('https://api.coingecko.com/api/v3/global', timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    global_data = data.get('data', {})
                    
                    total_market_cap = global_data.get('total_market_cap', {}).get('usd', 0)
                    btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
                    eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
                    
                    ultimate_data.append(f"🌍 Total Market Cap: ${total_market_cap:,.0f}")
                    ultimate_data.append(f"👑 BTC Dominance: {btc_dominance:.1f}%")
                    ultimate_data.append(f"⚡ ETH Dominance: {eth_dominance:.1f}%")
        except Exception as e:
            logger.error(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Ошибка глобальных данных: {e}")
    
    if not ultimate_data:
        ultimate_data = ["📊 Не удалось получить расширенные данные"]
        logger.warning("[УЛЬТИМЕЙТ-ДАННЫЕ] Не получено данных, используем fallback")
    
    result = "\\n".join(ultimate_data)
    logger.info(f"[УЛЬТИМЕЙТ-ДАННЫЕ] Собрано {len(ultimate_data)} строк данных")
    return result
'''

# Вставляем функцию после функции analyze_trading_chart
insert_position = content.find('async def cryptosud_analysis(')
content = content[:insert_position] + ultimate_data_function + '\n' + content[insert_position:]

# Обновляем функцию cryptosud_analysis для использования ультимейт данных
old_crypto_news_call = '''        # 2. Парсинг криптоновостей
        await send_telegram_message(chat_id, "📰 Собираю актуальные данные рынка...", None)
        crypto_news = await fetch_crypto_news(crypto_terms)'''

new_crypto_news_call = '''        # 2. Парсинг криптоновостей и максимальных данных
        await send_telegram_message(chat_id, "📰 Собираю МАКСИМУМ данных о рынке...", None)
        crypto_news = await fetch_crypto_news(crypto_terms)
        
        # 2.1. Получаем ультимейт данные
        await send_telegram_message(chat_id, "🚀 Подключаю дополнительные источники данных...", None)
        ultimate_data = await fetch_ultimate_crypto_data(crypto_terms)
        
        # Объединяем все данные
        full_market_data = f"{crypto_news}\\n\\n🔥 РАСШИРЕННЫЕ ДАННЫЕ:\\n{ultimate_data}"'''

content = content.replace(old_crypto_news_call, new_crypto_news_call)

# Обновляем все промпты для использования полных данных
content = content.replace('📰 Рыночные данные:\\n{crypto_news}', '📰 Полные рыночные данные:\\n{full_market_data}')

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Добавлен максимальный сбор криптоданных из множественных источников!")