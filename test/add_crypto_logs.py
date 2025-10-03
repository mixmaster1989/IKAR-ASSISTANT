import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем функцию fetch_crypto_news
old_function = '''async def fetch_crypto_news(crypto_terms):
    """Парсинг криптоновостей по найденным терминам."""
    import aiohttp
    import json
    
    try:
        # Используем CoinGecko API для получения новостей
        news_data = []
        
        # Простой парсинг новостей через RSS или API
        async with aiohttp.ClientSession() as session:
            # Пример запроса к CoinGecko trending
            try:
                async with session.get('https://api.coingecko.com/api/v3/search/trending', timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        trending = data.get('coins', [])
                        for coin in trending[:5]:  # Топ 5 трендовых
                            coin_data = coin.get('item', {})
                            news_data.append(f"📈 Trending: {coin_data.get('name', 'Unknown')} ({coin_data.get('symbol', 'N/A')})")
            except:
                pass
            
            # Добавляем общую информацию о рынке
            try:
                async with session.get('https://api.coingecko.com/api/v3/global', timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        global_data = data.get('data', {})
                        market_cap = global_data.get('total_market_cap', {}).get('usd', 0)
                        btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
                        news_data.append(f"💰 Общая капитализация: ${market_cap:,.0f}")
                        news_data.append(f"₿ Доминация Bitcoin: {btc_dominance:.1f}%")
            except:
                pass
        
        if not news_data:
            news_data = ["📊 Актуальные данные временно недоступны"]
        
        return "\\n".join(news_data)
        
    except Exception as e:
        logger.error(f"Ошибка парсинга криптоновостей: {e}")
        return "📊 Не удалось получить актуальные данные о рынке"'''

new_function = '''async def fetch_crypto_news(crypto_terms):
    """Парсинг криптоновостей по найденным терминам."""
    import aiohttp
    import json
    
    logger.info(f"[КРИПТОНОВОСТИ] Начинаю парсинг для терминов: {crypto_terms[:5]}")
    
    try:
        # Используем CoinGecko API для получения новостей
        news_data = []
        
        # Простой парсинг новостей через RSS или API
        async with aiohttp.ClientSession() as session:
            # Пример запроса к CoinGecko trending
            try:
                logger.info("[КРИПТОНОВОСТИ] Запрашиваю трендовые монеты с CoinGecko...")
                async with session.get('https://api.coingecko.com/api/v3/search/trending', timeout=10) as response:
                    logger.info(f"[КРИПТОНОВОСТИ] Trending API статус: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        trending = data.get('coins', [])
                        logger.info(f"[КРИПТОНОВОСТИ] Получено {len(trending)} трендовых монет")
                        for coin in trending[:5]:  # Топ 5 трендовых
                            coin_data = coin.get('item', {})
                            coin_name = coin_data.get('name', 'Unknown')
                            coin_symbol = coin_data.get('symbol', 'N/A')
                            news_data.append(f"📈 Trending: {coin_name} ({coin_symbol})")
                            logger.info(f"[КРИПТОНОВОСТИ] Добавлена монета: {coin_name} ({coin_symbol})")
                    else:
                        logger.warning(f"[КРИПТОНОВОСТИ] Trending API вернул статус {response.status}")
            except Exception as e:
                logger.error(f"[КРИПТОНОВОСТИ] Ошибка при запросе трендовых монет: {e}")
            
            # Добавляем общую информацию о рынке
            try:
                logger.info("[КРИПТОНОВОСТИ] Запрашиваю глобальные данные рынка...")
                async with session.get('https://api.coingecko.com/api/v3/global', timeout=10) as response:
                    logger.info(f"[КРИПТОНОВОСТИ] Global API статус: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        global_data = data.get('data', {})
                        market_cap = global_data.get('total_market_cap', {}).get('usd', 0)
                        btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
                        news_data.append(f"💰 Общая капитализация: ${market_cap:,.0f}")
                        news_data.append(f"₿ Доминация Bitcoin: {btc_dominance:.1f}%")
                        logger.info(f"[КРИПТОНОВОСТИ] Капитализация: ${market_cap:,.0f}, BTC доминация: {btc_dominance:.1f}%")
                    else:
                        logger.warning(f"[КРИПТОНОВОСТИ] Global API вернул статус {response.status}")
            except Exception as e:
                logger.error(f"[КРИПТОНОВОСТИ] Ошибка при запросе глобальных данных: {e}")
        
        if not news_data:
            news_data = ["📊 Актуальные данные временно недоступны"]
            logger.warning("[КРИПТОНОВОСТИ] Не получено данных, используем fallback")
        
        result = "\\n".join(news_data)
        logger.info(f"[КРИПТОНОВОСТИ] Итоговые данные ({len(news_data)} строк): {result[:100]}...")
        return result
        
    except Exception as e:
        logger.error(f"[КРИПТОНОВОСТИ] Общая ошибка парсинга: {e}")
        return "📊 Не удалось получить актуальные данные о рынке"'''

# Заменяем
content = content.replace(old_function, new_function)

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Добавлены подробные логи в функцию парсинга криптоновостей!")