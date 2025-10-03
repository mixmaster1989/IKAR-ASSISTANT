import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим функцию process_telegram_photo_with_crypto_detection и модифицируем её
old_crypto_detection = '''            if is_crypto:
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
                    logger.error(f"[КРИПТОДЕТЕКТОР] ❌ Ошибка в КРИПТОСУДЕ: {e}")'''

new_crypto_detection = '''            if is_crypto:
                logger.info(f"[КРИПТОДЕТЕКТОР] ✅ ОБНАРУЖЕН КРИПТОКОНТЕНТ! Запускаю специализированный анализ...")
                logger.info(f"[КРИПТОДЕТЕКТОР] Найденные термины: {crypto_terms}")
                
                # Уведомляем пользователей о начале специализированного анализа
                await send_telegram_message(chat_id, "🔍 Обнаружен криптограф! Запускаю специализированный анализ...", None)
                
                # Получаем путь к скачанному изображению
                temp_image_path = None
                photos = message.get("photo", [])
                if photos:
                    photo = photos[-1]  # Берем самое большое изображение
                    file_id = photo.get("file_id")
                    if file_id:
                        temp_image_path = await download_telegram_file(file_id)
                
                # СПЕЦИАЛИЗИРОВАННЫЙ АНАЛИЗ ГРАФИКА
                detailed_chart_analysis = None
                if temp_image_path:
                    await send_telegram_message(chat_id, "📊 Анализирую график специализированной моделью...", None)
                    logger.info("[КРИПТОДЕТЕКТОР] Запускаю специализированный анализ торгового графика...")
                    detailed_chart_analysis = await analyze_trading_chart(temp_image_path)
                    
                    if detailed_chart_analysis:
                        await send_telegram_message(chat_id, "✅ Специализированный анализ завершен! Запускаю КРИПТОСУД...", None)
                    else:
                        await send_telegram_message(chat_id, "⚠️ Специализированный анализ недоступен, продолжаю с базовым...", None)
                    
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
                    logger.error(f"[КРИПТОДЕТЕКТОР] ❌ Ошибка в КРИПТОСУДЕ: {e}")'''

content = content.replace(old_crypto_detection, new_crypto_detection)

# Теперь модифицируем функцию cryptosud_analysis для отображения процессов
old_cryptosud_start = '''        # 1. Уведомление о запуске
        await send_telegram_message(chat_id, "🚨 ВНИМАНИЕ! ОБНАРУЖЕН КРИПТОГРАФ!", None)
        await send_telegram_message(chat_id, f"🔍 Найденные термины: {', '.join(crypto_terms[:5])}", None)
        await send_telegram_message(chat_id, "⚖️ ЗАПУСКАЕТСЯ КРИПТОСУД!", None)'''

new_cryptosud_start = '''        # 1. Уведомление о запуске с отображением процессов
        await send_telegram_message(chat_id, "🚨 ВНИМАНИЕ! ОБНАРУЖЕН КРИПТОГРАФ!", None)
        await send_telegram_message(chat_id, f"🔍 Найденные термины: {', '.join(crypto_terms[:5])}", None)
        
        # Показываем результаты специализированного анализа
        if detailed_chart_analysis:
            await send_telegram_message(chat_id, "📊 СПЕЦИАЛИЗИРОВАННЫЙ АНАЛИЗ ГРАФИКА ПОЛУЧЕН!", None)
            # Отправляем краткую выжимку специализированного анализа
            analysis_preview = detailed_chart_analysis[:300] + "..." if len(detailed_chart_analysis) > 300 else detailed_chart_analysis
            await send_telegram_message(chat_id, f"📈 Краткий анализ графика:\\n{analysis_preview}", None)
        else:
            await send_telegram_message(chat_id, "⚠️ Специализированный анализ недоступен, работаю с базовым описанием", None)
        
        await send_telegram_message(chat_id, "⚖️ ЗАПУСКАЕТСЯ КРИПТОСУД!", None)'''

content = content.replace(old_cryptosud_start, new_cryptosud_start)

# Улучшаем отображение процессов в КРИПТОСУДЕ
old_market_data = '''        # 2. Парсинг криптоновостей и максимальных данных
        await send_telegram_message(chat_id, "📰 Собираю МАКСИМУМ данных о рынке...", None)
        crypto_news = await fetch_crypto_news(crypto_terms)
        
        # 2.1. Получаем ультимейт данные
        await send_telegram_message(chat_id, "🚀 Подключаю дополнительные источники данных...", None)
        ultimate_data = await fetch_ultimate_crypto_data(crypto_terms)
        
        # Объединяем все данные
        full_market_data = f"{crypto_news}\\n\\n🔥 РАСШИРЕННЫЕ ДАННЫЕ:\\n{ultimate_data}"'''

new_market_data = '''        # 2. Парсинг криптоновостей и максимальных данных
        await send_telegram_message(chat_id, "📰 Собираю МАКСИМУМ данных о рынке...", None)
        crypto_news = await fetch_crypto_news(crypto_terms)
        
        # 2.1. Получаем ультимейт данные
        await send_telegram_message(chat_id, "🚀 Подключаю 6 источников данных (Binance, CoinGecko, F&G Index...)...", None)
        ultimate_data = await fetch_ultimate_crypto_data(crypto_terms)
        
        # Объединяем все данные
        full_market_data = f"{crypto_news}\\n\\n🔥 РАСШИРЕННЫЕ ДАННЫЕ:\\n{ultimate_data}"
        
        await send_telegram_message(chat_id, "✅ Данные собраны! Начинаю анализ экспертов...", None)'''

content = content.replace(old_market_data, new_market_data)

# Добавляем отображение прогресса для каждого эксперта
progress_messages = [
    ('🐂 Формирую БЫЧЬЮ позицию...', '🐂 Бычий аналитик завершил анализ!'),
    ('🐻 Формирую МЕДВЕЖЬЮ позицию...', '🐻 Медвежий аналитик завершил анализ!'),
    ('📊 Технический анализ от судьи...', '📊 Технический судья вынес вердикт!'),
    ('🌍 Макроэкономический анализ...', '🌍 Макроэксперт завершил глобальный анализ!'),
    ('😂 Добавляю криптомемы...', '😂 Криптомемы готовы!'),
    ('💰 Формирую торговый сигнал...', '💰 Торговый сигнал сформирован!')
]

# Заменяем каждое сообщение о начале на пару начало-завершение
for start_msg, end_msg in progress_messages:
    # Находим паттерн: await send_telegram_message(chat_id, "start_msg", None)
    # За которым следует вызов LLM и отправка результата
    pattern = f'await send_telegram_message\\(chat_id, "{re.escape(start_msg)}", None\\)'
    
    if pattern.replace('\\', '') in content:
        # Находим следующий await send_long_telegram_message после этого сообщения
        start_pos = content.find(start_msg)
        if start_pos != -1:
            # Ищем следующий send_long_telegram_message
            next_long_msg_pos = content.find('await send_long_telegram_message(chat_id, f"', start_pos)
            if next_long_msg_pos != -1:
                # Вставляем сообщение о завершении перед отправкой результата
                insert_pos = next_long_msg_pos
                completion_msg = f'        await send_telegram_message(chat_id, "{end_msg}", None)\n        '
                content = content[:insert_pos] + completion_msg + content[insert_pos:]

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Добавлен специализированный анализ графиков с отображением процессов для пользователей!")