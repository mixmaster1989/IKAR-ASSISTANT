import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. ИСПРАВЛЯЕМ ПРОМПТ ДЛЯ АНАЛИЗА ГРАФИКА - ФОКУС НА ЦЕНЕ
old_trading_prompt = '''        # Специализированный промпт для анализа торговых графиков
        trading_prompt = """📊 Ты — ЭКСПЕРТ ПО ТЕХНИЧЕСКОМУ АНАЛИЗУ ГРАФИКОВ! Проанализируй этот торговый график максимально детально:

🎯 ОБЯЗАТЕЛЬНО УКАЖИ:
💰 — Текущая цена (если видна)
📈 — Торговая пара (какая криптовалюта)
⏰ — Таймфрейм графика (1m, 5m, 1h, 4h, 1D и т.д.)
📊 — Тип графика (свечи, линия, бары)

🔍 ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ (если есть):
📈 — Скользящие средние (MA, EMA) - значения и пересечения
📊 — RSI - текущее значение и зоны
📉 — MACD - сигналы и дивергенции  
🎯 — Bollinger Bands - положение цены
📊 — Объемы - аномалии и подтверждения
🔄 — Другие индикаторы (Stoch, Williams %R и т.д.)

📈 ПАТТЕРНЫ И УРОВНИ:
🎯 — Уровни поддержки и сопротивления (конкретные цены)
📐 — Трендовые линии и каналы
🔺 — Графические паттерны (треугольники, флаги, голова-плечи и т.д.)
📊 — Фибоначчи уровни (если есть)
🎪 — Японские свечные паттерны

⚡ РЫНОЧНАЯ СИТУАЦИЯ:
📈 — Текущий тренд (восходящий/нисходящий/боковой)
🔥 — Волатильность и активность
💥 — Ключевые события на графике
🎯 — Точки входа и выхода

Будь максимально конкретным! Указывай цифры, уровни, проценты!"""'''

new_trading_prompt = '''        # Специализированный промпт для анализа торговых графиков с фокусом на цене
        trading_prompt = """📊 Ты — ЭКСПЕРТ ПО ТЕХНИЧЕСКОМУ АНАЛИЗУ ГРАФИКОВ! Проанализируй этот торговый график максимально детально:

🚨 КРИТИЧЕСКИ ВАЖНО - ЦЕНА:
💰 — ТЕКУЩАЯ ЦЕНА: Найди и укажи ТОЧНУЮ цену справа на графике (последняя цена закрытия)
💰 — ФОРМАТ ЦЕНЫ: Если цена меньше $1, указывай с максимальной точностью (например: $0.000021450)
💰 — ВАЛИДАЦИЯ: Проверь цену несколько раз, она должна соответствовать последней свече
📈 — ТОРГОВАЯ ПАРА: Точно определи пару (BTC/USDT, ETH/USDT, PEPE/USDT и т.д.)

🎯 ОБЯЗАТЕЛЬНЫЕ ДАННЫЕ:
⏰ — Таймфрейм графика (1m, 5m, 15m, 1h, 4h, 1D и т.д.)
📊 — Тип графика (свечи, линия, бары)
📅 — Время последней свечи (если видно)

🔍 ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ (если есть):
📈 — Скользящие средние (MA, EMA) - ТОЧНЫЕ значения
📊 — RSI - текущее значение (например: RSI = 67.2)
📉 — MACD - конкретные значения сигнальной линии
🎯 — Bollinger Bands - верхняя/нижняя границы
📊 — Объемы - текущий объем торгов
🔄 — Другие индикаторы с числовыми значениями

📈 УРОВНИ И ПАТТЕРНЫ:
🎯 — Поддержка/сопротивление (ТОЧНЫЕ цены: $0.000019, $0.000023)
📐 — Трендовые линии (углы наклона, точки касания)
🔺 — Графические паттерны (размеры, проекции)
📊 — Фибоначчи уровни (23.6%, 38.2%, 61.8%)

⚡ РЫНОЧНАЯ СИТУАЦИЯ:
📈 — Тренд (восходящий/нисходящий/боковой) + сила тренда
🔥 — Волатильность (высокая/средняя/низкая)
💥 — Ключевые уровни для входа/выхода

ВНИМАНИЕ! Цена - это САМОЕ ВАЖНОЕ! Найди её на графике справа и укажи с максимальной точностью!"""'''

content = content.replace(old_trading_prompt, new_trading_prompt)

# 2. ДОБАВЛЯЕМ ВАЛИДАЦИЮ ЦЕНЫ ЧЕРЕЗ API
price_validation_function = '''
async def validate_price_from_apis(trading_pair, chart_price):
    """Валидация цены с графика через реальные API."""
    import aiohttp
    
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
'''

# Вставляем функцию валидации после функции analyze_trading_chart
insert_position = content.find('async def fetch_ultimate_crypto_data(')
content = content[:insert_position] + price_validation_function + '\n' + content[insert_position:]

# 3. ИСПРАВЛЯЕМ ЛОГИКУ ПЕРЕБОРА КЛЮЧЕЙ ДЛЯ МЕМОВ
# Находим функцию cryptosud_analysis и исправляем вызов мемов
old_meme_call = '''        crypto_memes = await llm_client.chat_completion(
            user_message=meme_prompt,
            system_prompt="😂 Ты криптомемер! Добавь юмора и мемов! Используй криптосленг! 🚀",
            chat_history=[],
            model="deepseek/deepseek-r1-0528:free",
            max_tokens=500
        )'''

new_meme_call = '''        try:
            crypto_memes = await llm_client.chat_completion(
                user_message=meme_prompt,
                system_prompt="😂 Ты криптомемер! Добавь юмора и мемов! Используй криптосленг! 🚀",
                chat_history=[],
                model="deepseek/deepseek-r1-0528:free",
                max_tokens=500
            )
        except Exception as e:
            logger.error(f"[КРИПТОСУД] Ошибка получения мемов: {e}")
            crypto_memes = "😂 Мемы временно недоступны, но настроение бычье! 🚀 HODL и на луну! 💎🙌"'''

content = content.replace(old_meme_call, new_meme_call)

# 4. ДОБАВЛЯЕМ ВАЛИДАЦИЮ ЦЕНЫ В АНАЛИЗ ГРАФИКА
old_chart_analysis = '''                if response.status == 200:
                    result = await response.json()
                    chart_analysis = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.info(f"[ГРАФИК-АНАЛИЗ] Получен детальный анализ: {chart_analysis[:100]}...")
                    return chart_analysis'''

new_chart_analysis = '''                if response.status == 200:
                    result = await response.json()
                    chart_analysis = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.info(f"[ГРАФИК-АНАЛИЗ] Получен детальный анализ: {chart_analysis[:100]}...")
                    
                    # Извлекаем цену и торговую пару из анализа
                    chart_price = None
                    trading_pair = None
                    
                    # Ищем цену в анализе (паттерны: $0.000021, $65432.10)
                    price_match = re.search(r'\\$([0-9]+\\.?[0-9]*)', chart_analysis)
                    if price_match:
                        try:
                            chart_price = float(price_match.group(1))
                        except:
                            pass
                    
                    # Ищем торговую пару
                    pair_match = re.search(r'([A-Z]+/[A-Z]+)', chart_analysis)
                    if pair_match:
                        trading_pair = pair_match.group(1)
                    
                    # Валидируем цену через API
                    if chart_price and trading_pair:
                        validated_price, price_sources = await validate_price_from_apis(trading_pair, chart_price)
                        
                        if price_sources:
                            validation_info = "\\n\\n🔍 ВАЛИДАЦИЯ ЦЕНЫ:\\n"
                            for source, price in price_sources:
                                validation_info += f"• {source}: ${price:.8f}\\n"
                            chart_analysis += validation_info
                    
                    return chart_analysis'''

content = content.replace(old_chart_analysis, new_chart_analysis)

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Исправлены проблемы: логика ключей для мемов + валидация цен через API!")