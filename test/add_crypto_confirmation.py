import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Добавляем словарь для хранения ожидающих подтверждения запросов
pending_crypto_requests = '''
# Словарь для хранения ожидающих подтверждения КРИПТОСУДА
pending_crypto_requests = {}
'''

# Вставляем после импортов
insert_position = content.find('logger = logging.getLogger("chatumba.telegram_polling")')
content = content[:insert_position] + pending_crypto_requests + '\n' + content[insert_position:]

# 2. Заменяем логику детекции крипто на отправку кнопок
old_crypto_detection = '''            if is_crypto:
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

new_crypto_detection = '''            if is_crypto:
                logger.info(f"[КРИПТОДЕТЕКТОР] ✅ ОБНАРУЖЕН КРИПТОКОНТЕНТ! Отправляю кнопки подтверждения...")
                logger.info(f"[КРИПТОДЕТЕКТОР] Найденные термины: {crypto_terms}")
                
                # Сохраняем данные для последующего анализа
                request_id = f"{chat_id}_{int(datetime.now().timestamp())}"
                pending_crypto_requests[request_id] = {
                    'chat_id': chat_id,
                    'image_description': image_description,
                    'crypto_terms': crypto_terms,
                    'message': message,
                    'timestamp': datetime.now()
                }
                
                # Отправляем сообщение с кнопками
                from api.telegram import send_telegram_message_with_buttons
                
                buttons = [
                    [{"text": "✅ ДА - Запустить КРИПТОСУД", "callback_data": f"crypto_yes_{request_id}"}],
                    [{"text": "❌ НЕТ - Пропустить", "callback_data": f"crypto_no_{request_id}"}]
                ]
                
                terms_text = ', '.join(crypto_terms[:5])
                confirmation_text = (
                    f"🔍 **ОБНАРУЖЕН КРИПТОГРАФ!**\\n\\n"
                    f"📊 Найденные термины: {terms_text}\\n\\n"
                    f"⚠️ КРИПТОСУД потребляет много ресурсов.\\n"
                    f"Запустить полный анализ?"
                )
                
                await send_telegram_message_with_buttons(chat_id, confirmation_text, buttons)
                logger.info(f"[КРИПТОДЕТЕКТОР] Отправлены кнопки подтверждения для {request_id}")'''

content = content.replace(old_crypto_detection, new_crypto_detection)

# 3. Убираем этап с мемами из cryptosud_analysis
old_memes_section = '''        # 7. КРИПТОМЕМЫ И ЮМОР
        await send_telegram_message(chat_id, "😂 Добавляю криптомемы...", None)
        
        meme_prompt = f"""😂 Ты — КРИПТОМЕМЕР! Знаешь все мемы и шутки! 🚀

🤡 На основе всего этого криптоцирка, напиши:
😄 — Смешной комментарий про ходлеров
🎪 — Мем про быков и медведей
🤪 — Шутку про "это дно" или "на луну"
💎 — Совет в стиле криптомемов

🎨 Используй криптосленг, эмодзи и мемы! 😂

Весь этот криптоанализ выше..."""
        
        try:
            crypto_memes = await llm_client.chat_completion(
                user_message=meme_prompt,
                system_prompt="😂 Ты криптомемер! Добавь юмора и мемов! Используй криптосленг! 🚀",
                chat_history=[],
                model="deepseek/deepseek-r1-0528:free",
                max_tokens=500
            )
        except Exception as e:
            logger.error(f"[КРИПТОСУД] Ошибка получения мемов: {e}")
            crypto_memes = "😂 Мемы временно недоступны, но настроение бычье! 🚀 HODL и на луну! 💎🙌"
        
        await send_telegram_message(chat_id, "😂 Криптомемы готовы!", None)
        await send_long_telegram_message(chat_id, f"😂 **КРИПТОМЕМЫ:**\\n{crypto_memes}", None)
        
        # 8. ТОРГОВЫЙ СИГНАЛ - ФИНАЛЬНАЯ СДЕЛКА'''

new_trading_section = '''        # 7. ТОРГОВЫЙ СИГНАЛ - ФИНАЛЬНАЯ СДЕЛКА'''

content = content.replace(old_memes_section, new_trading_section)

# 4. Обновляем нумерацию в торговом сигнале
content = content.replace('# 8. ТОРГОВЫЙ СИГНАЛ - ФИНАЛЬНАЯ СДЕЛКА', '# 7. ТОРГОВЫЙ СИГНАЛ - ФИНАЛЬНАЯ СДЕЛКА')

# 5. Убираем ссылки на мемы в торговом промпте
old_trading_prompt = '''🐂 Бычий анализ: {bull_opinion}

🐻 Медвежий анализ: {bear_opinion}

📊 Технический анализ: {tech_analysis}

🌍 Макроанализ: {macro_analysis}

📰 Рыночные данные: {crypto_news}"""'''

new_trading_prompt = '''🐂 Бычий анализ: {bull_opinion}

🐻 Медвежий анализ: {bear_opinion}

📊 Технический анализ: {tech_analysis}

🌍 Макроанализ: {macro_analysis}

📰 Рыночные данные: {full_market_data}"""'''

content = content.replace(old_trading_prompt, new_trading_prompt)

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Добавлены кнопки подтверждения для КРИПТОСУДА и убраны мемы!")