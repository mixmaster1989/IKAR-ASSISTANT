import re

# Читаем файл telegram_polling.py
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем обработку callback_query в основной цикл
old_update_handling = '''            for update in updates:
                if "message" in update:'''

new_update_handling = '''            for update in updates:
                # Обработка callback_query (нажатия кнопок)
                if "callback_query" in update:
                    callback_query = update["callback_query"]
                    callback_data = callback_query.get("data", "")
                    chat_id = str(callback_query["message"]["chat"]["id"])
                    message_id = callback_query["message"]["message_id"]
                    
                    logger.info(f"[CALLBACK] Получен callback: {callback_data} в чате {chat_id}")
                    
                    # Обработка подтверждения КРИПТОСУДА
                    if callback_data.startswith("crypto_"):
                        await handle_crypto_callback(callback_query, callback_data, chat_id, message_id)
                    
                    continue
                
                if "message" in update:'''

content = content.replace(old_update_handling, new_update_handling)

# Добавляем функцию обработки crypto callback'ов
callback_handler = '''
async def handle_crypto_callback(callback_query, callback_data, chat_id, message_id):
    """Обрабатывает callback от кнопок подтверждения КРИПТОСУДА."""
    from api.telegram import send_telegram_message, llm_client
    
    try:
        # Отвечаем на callback чтобы убрать "загрузку" на кнопке
        callback_id = callback_query["id"]
        answer_url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/answerCallbackQuery"
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post(answer_url, json={"callback_query_id": callback_id})
        
        # Парсим callback_data
        parts = callback_data.split("_")
        if len(parts) < 3:
            logger.error(f"[CALLBACK] Неверный формат callback_data: {callback_data}")
            return
        
        action = parts[1]  # yes или no
        request_id = "_".join(parts[2:])  # остальная часть ID
        
        logger.info(f"[CALLBACK] Действие: {action}, Request ID: {request_id}")
        
        # Проверяем есть ли запрос в pending_crypto_requests
        if request_id not in pending_crypto_requests:
            await send_telegram_message(chat_id, "⚠️ Запрос устарел или уже обработан", None)
            logger.warning(f"[CALLBACK] Запрос {request_id} не найден в pending_crypto_requests")
            return
        
        request_data = pending_crypto_requests[request_id]
        
        if action == "yes":
            # Пользователь подтвердил - запускаем КРИПТОСУД
            await send_telegram_message(chat_id, "✅ Запускаю КРИПТОСУД! Это займет несколько минут...", None)
            
            # Получаем данные из сохраненного запроса
            image_description = request_data['image_description']
            crypto_terms = request_data['crypto_terms']
            message = request_data['message']
            
            # Скачиваем изображение для специализированного анализа
            temp_image_path = None
            photos = message.get("photo", [])
            if photos:
                photo = photos[-1]
                file_id = photo.get("file_id")
                if file_id:
                    from api.telegram import download_telegram_file
                    temp_image_path = await download_telegram_file(file_id)
            
            # Специализированный анализ графика
            detailed_chart_analysis = None
            if temp_image_path:
                await send_telegram_message(chat_id, "📊 Анализирую график специализированной моделью...", None)
                detailed_chart_analysis = await analyze_trading_chart(temp_image_path)
                
                # Удаляем временный файл
                try:
                    import os
                    os.remove(temp_image_path)
                except:
                    pass
            
            # Запускаем КРИПТОСУД
            try:
                await cryptosud_analysis(chat_id, image_description, crypto_terms, detailed_chart_analysis)
                logger.info(f"[CALLBACK] ✅ КРИПТОСУД успешно завершен для {request_id}")
            except Exception as e:
                logger.error(f"[CALLBACK] ❌ Ошибка в КРИПТОСУДЕ: {e}")
                await send_telegram_message(chat_id, f"❌ Ошибка при выполнении КРИПТОСУДА: {e}", None)
        
        elif action == "no":
            # Пользователь отказался
            await send_telegram_message(chat_id, "❌ КРИПТОСУД отменен. Ресурсы сохранены!", None)
            logger.info(f"[CALLBACK] Пользователь отказался от КРИПТОСУДА для {request_id}")
        
        # Удаляем запрос из pending
        del pending_crypto_requests[request_id]
        logger.info(f"[CALLBACK] Запрос {request_id} удален из pending")
        
    except Exception as e:
        logger.error(f"[CALLBACK] Ошибка обработки callback: {e}")
        await send_telegram_message(chat_id, "❌ Ошибка при обработке запроса", None)
'''

# Вставляем обработчик после функций анализа
insert_position = content.find('async def process_telegram_photo_with_crypto_detection(')
content = content[:insert_position] + callback_handler + '\n' + content[insert_position:]

# Добавляем импорт TELEGRAM_CONFIG в начало файла
if 'from config import TELEGRAM_CONFIG' not in content:
    import_position = content.find('from pathlib import Path')
    content = content[:import_position] + 'from config import TELEGRAM_CONFIG\n' + content[import_position:]

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Добавлена обработка callback'ов для кнопок подтверждения КРИПТОСУДА!")