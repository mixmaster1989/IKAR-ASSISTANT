import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем функцию продвинутого анализа графика
advanced_analysis_function = '''
async def analyze_trading_chart(image_path):
    """Продвинутый анализ торгового графика с помощью специализированной модели."""
    import aiohttp
    import json
    import base64
    
    logger.info("[ГРАФИК-АНАЛИЗ] Начинаю продвинутый анализ торгового графика...")
    
    try:
        # Конвертируем изображение в base64
        with open(image_path, 'rb') as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Специализированный промпт для анализа торговых графиков
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

Будь максимально конкретным! Указывай цифры, уровни, проценты!"""

        # Отправляем запрос к специализированной модели для анализа графиков
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "qwen/qwen2.5-vl-72b-instruct:free",
                "messages": [
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": trading_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000
            }
            
            headers = {
                "Authorization": "Bearer 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",
                "Content-Type": "application/json"
            }
            
            logger.info("[ГРАФИК-АНАЛИЗ] Отправляю запрос к qwen2.5-vl-72b...")
            
            async with session.post("https://openrouter.ai/api/v1/chat/completions", 
                                  json=payload, headers=headers, timeout=30) as response:
                logger.info(f"[ГРАФИК-АНАЛИЗ] Статус ответа: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    chart_analysis = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.info(f"[ГРАФИК-АНАЛИЗ] Получен детальный анализ: {chart_analysis[:100]}...")
                    return chart_analysis
                else:
                    error_text = await response.text()
                    logger.error(f"[ГРАФИК-АНАЛИЗ] Ошибка API: {response.status} - {error_text}")
                    return None
                    
    except Exception as e:
        logger.error(f"[ГРАФИК-АНАЛИЗ] Ошибка при анализе графика: {e}")
        return None
'''

# Вставляем функцию после функции fetch_crypto_news
insert_position = content.find('async def cryptosud_analysis(')
content = content[:insert_position] + advanced_analysis_function + '\n' + content[insert_position:]

# Теперь модифицируем функцию process_telegram_photo_with_crypto_detection
old_detection_logic = '''        if image_description:
            logger.info(f"[КРИПТОДЕТЕКТОР] Полное описание: {image_description}")
            # Проверяем на криптоконтент
            is_crypto, crypto_terms = detect_crypto_content(image_description)
            
            logger.info(f"[КРИПТОДЕТЕКТОР] Результат детекции: is_crypto={is_crypto}, terms={crypto_terms}")
            
            if is_crypto:
                logger.info(f"[КРИПТОДЕТЕКТОР] ✅ ОБНАРУЖЕН КРИПТОКОНТЕНТ! Запускаю КРИПТОСУД для группы {chat_id}")
                logger.info(f"[КРИПТОДЕТЕКТОР] Найденные термины: {crypto_terms}")
                # Запускаем КРИПТОСУД!
                try:
                    await cryptosud_analysis(chat_id, image_description, crypto_terms)
                    logger.info(f"[КРИПТОДЕТЕКТОР] ✅ КРИПТОСУД успешно завершен для группы {chat_id}")
                except Exception as e:
                    logger.error(f"[КРИПТОДЕТЕКТОР] ❌ Ошибка в КРИПТОСУДЕ: {e}")
            else:
                logger.info(f"[КРИПТОДЕТЕКТОР] ❌ Криптоконтент не обнаружен в группе {chat_id}")'''

new_detection_logic = '''        if image_description:
            logger.info(f"[КРИПТОДЕТЕКТОР] Полное описание: {image_description}")
            # Проверяем на криптоконтент
            is_crypto, crypto_terms = detect_crypto_content(image_description)
            
            logger.info(f"[КРИПТОДЕТЕКТОР] Результат детекции: is_crypto={is_crypto}, terms={crypto_terms}")
            
            if is_crypto:
                logger.info(f"[КРИПТОДЕТЕКТОР] ✅ ОБНАРУЖЕН КРИПТОКОНТЕНТ! Запускаю продвинутый анализ...")
                logger.info(f"[КРИПТОДЕТЕКТОР] Найденные термины: {crypto_terms}")
                
                # Получаем путь к скачанному изображению из process_telegram_photo
                import tempfile
                temp_image_path = None
                
                # Скачиваем изображение еще раз для продвинутого анализа
                photos = message.get("photo", [])
                if photos:
                    photo = photos[-1]  # Берем самое большое изображение
                    file_id = photo.get("file_id")
                    if file_id:
                        temp_image_path = await download_telegram_file(file_id)
                
                # Продвинутый анализ графика
                detailed_chart_analysis = None
                if temp_image_path:
                    logger.info("[КРИПТОДЕТЕКТОР] Запускаю продвинутый анализ торгового графика...")
                    detailed_chart_analysis = await analyze_trading_chart(temp_image_path)
                    
                    # Удаляем временный файл
                    try:
                        os.remove(temp_image_path)
                    except:
                        pass
                
                # Запускаем КРИПТОСУД с двумя описаниями!
                try:
                    await cryptosud_analysis(chat_id, image_description, crypto_terms, detailed_chart_analysis)
                    logger.info(f"[КРИПТОДЕТЕКТОР] ✅ КРИПТОСУД успешно завершен для группы {chat_id}")
                except Exception as e:
                    logger.error(f"[КРИПТОДЕТЕКТОР] ❌ Ошибка в КРИПТОСУДЕ: {e}")
            else:
                logger.info(f"[КРИПТОДЕТЕКТОР] ❌ Криптоконтент не обнаружен в группе {chat_id}")'''

# Заменяем логику детекции
content = content.replace(old_detection_logic, new_detection_logic)

# Модифицируем функцию cryptosud_analysis для принятия дополнительного параметра
old_function_signature = 'async def cryptosud_analysis(chat_id, image_description, crypto_terms):'
new_function_signature = 'async def cryptosud_analysis(chat_id, image_description, crypto_terms, detailed_chart_analysis=None):'

content = content.replace(old_function_signature, new_function_signature)

# Добавляем использование детального анализа в промптах
old_bull_prompt = '''        bull_prompt = f"""🐂 Ты — БЫЧИЙ КРИПТОАНАЛИТИК! Оптимист и сторонник роста! 📈

🎯 Проанализируй график и рыночные данные с БЫЧЬЕЙ позиции:
💚 — Какие сигналы роста ты видишь?
🚀 — Почему цена пойдет ВВЕРХ?
💎 — Какие уровни для покупки?
📊 — Твой прогноз на ближайшее время?

🎨 Используй эмодзи, будь убедительным быком! 🐂

📷 Описание графика:
{image_description}

📰 Рыночные данные:
{crypto_news}"""'''

new_bull_prompt = '''        # Формируем полное описание графика
        full_chart_description = image_description
        if detailed_chart_analysis:
            full_chart_description += f"\\n\\n📊 ДЕТАЛЬНЫЙ ТЕХНИЧЕСКИЙ АНАЛИЗ:\\n{detailed_chart_analysis}"
        
        bull_prompt = f"""🐂 Ты — БЫЧИЙ КРИПТОАНАЛИТИК! Оптимист и сторонник роста! 📈

🎯 Проанализируй график и рыночные данные с БЫЧЬЕЙ позиции:
💚 — Какие сигналы роста ты видишь?
🚀 — Почему цена пойдет ВВЕРХ?
💎 — Какие уровни для покупки?
📊 — Твой прогноз на ближайшее время?

🎨 Используй эмодзи, будь убедительным быком! 🐂

📷 Анализ графика:
{full_chart_description}

📰 Рыночные данные:
{crypto_news}"""'''

content = content.replace(old_bull_prompt, new_bull_prompt)

# Аналогично для медвежьего промпта
old_bear_prompt = '''        bear_prompt = f"""🐻 Ты — МЕДВЕЖИЙ КРИПТОАНАЛИТИК! Реалист и скептик! 📉

🎯 Проанализируй график и рыночные данные с МЕДВЕЖЬЕЙ позиции:
❤️ — Какие сигналы падения ты видишь?
📉 — Почему цена пойдет ВНИЗ?
💸 — Какие риски и опасности?
📊 — Твой прогноз на коррекцию?

🎨 Используй эмодзи, будь осторожным медведем! 🐻

📷 Описание графика:
{image_description}

📰 Рыночные данные:
{crypto_news}"""'''

new_bear_prompt = '''        bear_prompt = f"""🐻 Ты — МЕДВЕЖИЙ КРИПТОАНАЛИТИК! Реалист и скептик! 📉

🎯 Проанализируй график и рыночные данные с МЕДВЕЖЬЕЙ позиции:
❤️ — Какие сигналы падения ты видишь?
📉 — Почему цена пойдет ВНИЗ?
💸 — Какие риски и опасности?
📊 — Твой прогноз на коррекцию?

🎨 Используй эмодзи, будь осторожным медведем! 🐻

📷 Анализ графика:
{full_chart_description}

📰 Рыночные данные:
{crypto_news}"""'''

content = content.replace(old_bear_prompt, new_bear_prompt)

# Обновляем технический и макро анализ
content = content.replace('📷 Описание графика:\\n{image_description}', '📷 Анализ графика:\\n{full_chart_description}')

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Добавлен продвинутый анализ торговых графиков в КРИПТОСУД!")