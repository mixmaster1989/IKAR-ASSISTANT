"""
Модуль для обработки Telegram polling.
Вынесен из telegram.py для улучшения структуры кода.
"""
import logging
import asyncio
import os
import sqlite3
from datetime import datetime, timedelta
from backend.config import TELEGRAM_CONFIG
from pathlib import Path
import re
from backend.api.telegram_photo_handler import send_photo_recognition_buttons, handle_photo_callback
from backend.memory.sqlite import sqlite_storage
# STABLE: текущая версия стабильна

# Словарь для хранения ожидающих подтверждения КРИПТОСУДА
pending_crypto_requests = {}

# Словарь для хранения сообщений с фото в группах
# pending_photo_messages больше не нужен, теперь всё в БД

logger = logging.getLogger("chatumba.telegram_polling")

def cleanup_old_photo_messages():
    """Очищает старые сообщения с фото из БД (старше 1 часа)."""
    try:
        sqlite_storage.cleanup_old_pending_photos(3600)
    except Exception as e:
        logger.error(f"Ошибка при очистке старых фото-сообщений из БД: {e}")

# Импортируем функцию для обработки фото
from .telegram_vision import process_telegram_photo
from .telegram_core import answer_callback_query, send_telegram_message_with_buttons, send_telegram_message

# Импортируем новые модули
from .telegram.message_handler import send_evolution_report, neurosud_analysis
from .telegram.group_handler import show_collective_memory, show_full_chunks_with_buttons, handle_chunk_deletion, handle_chunk_view

# Импортируем крипто-функции из нового модульного пакета
from .telegram.crypto import (
    detect_crypto_content,
    extract_trading_pair_from_description,
    fetch_ultimate_crypto_data,
    fetch_macro_economic_data,
    fetch_bingx_market_data,
    format_bingx_data_for_prompts,
    validate_price_from_apis,
    fetch_crypto_news,
    analyze_trading_chart,
    cryptosud_analysis
)

# Импортируем функции из telegram_crypto_processing
from .telegram_crypto_processing import (
    process_telegram_photo_with_crypto_detection,
    handle_crypto_callback
)

# Безопасный импорт BingX интеграции
from utils.import_helper import get_bingx_client, get_crypto_integration

# Криптотермины теперь импортируются из crypto_handler.py

# detect_crypto_content теперь импортируется из crypto_handler.py

# extract_trading_pair_from_description теперь импортируется из crypto_handler.py



# format_bingx_data_for_prompts теперь импортируется из telegram_crypto_processing.py








# validate_price_from_apis теперь импортируется из telegram_crypto_processing.py

# fetch_macro_economic_data теперь импортируется из telegram_crypto_processing.py










# Функция send_evolution_report вынесена в telegram/message_handler.py

# Функция show_collective_memory вынесена в telegram/group_handler.py

# Функция show_full_chunks_with_buttons вынесена в telegram/group_handler.py

# Функция handle_chunk_view вынесена в telegram/group_handler.py

# Функция neurosud_analysis вынесена в telegram/message_handler.py

async def telegram_polling():
    global monitoring_chat_id
    """Основной цикл polling для Telegram."""
    from api.telegram_core import (
        get_updates, monitoring_chat_id, TELEGRAM_CONFIG, 
        get_personality, sqlite_storage, process_telegram_message,
        send_telegram_message, send_monitoring_report, send_autonomous_message,
        send_autonomous_channel_message, send_channel_startup_message,
        check_channel_permissions, download_telegram_file, get_stt_engine,
        temp_dir, group_names_mode, analyze_group_history, get_bot_info,
        send_telegram_message_with_buttons,
        answer_callback_query
    )
    from api.telegram_vision import process_telegram_photo
    logger.info("🔄 Запуск Telegram polling...")
    bot_info = await get_bot_info()
    bot_id = None
    if bot_info:
        bot_id = bot_info.get("id")
    while True:
        try:
            # Очищаем старые фото-сообщения
            cleanup_old_photo_messages()
            
            updates = await get_updates()
            for update in updates:
                # Обработка callback_query (нажатия кнопок)
                if "callback_query" in update:
                    callback_query = update["callback_query"]
                    callback_data = callback_query.get("data", "")
                    chat_id = str(callback_query["message"]["chat"]["id"])
                    message_id = callback_query["message"]["message_id"]
                    from_user = callback_query.get("from", {})
                    user_id = str(from_user.get("id", ""))
                    logger.info(f"[CALLBACK] Получен callback: {callback_data} в чате {chat_id}")
                    # Обработка новых фото-кнопок
                    if callback_data.startswith("photo_img_") or callback_data.startswith("photo_text_"):
                        handled = await handle_photo_callback(callback_query, callback_data, chat_id, message_id, user_id, temp_dir, download_telegram_file)
                        if handled:
                            continue
                    # Обработка подтверждения КРИПТОСУДА
                    if callback_data.startswith("crypto_"):
                        await handle_crypto_callback(callback_query, callback_data, chat_id, message_id)
                        continue
                    
                    # Обработка кнопок подтверждения бота
                    if callback_data.startswith("bot_confirm_"):
                        try:
                            from api.smart_bot_trigger import smart_bot_trigger
                            
                            # Парсим callback_data: bot_confirm_yes_12345678 или bot_confirm_no_12345678
                            parts = callback_data.split("_")
                            if len(parts) >= 4:
                                answer = parts[2]  # yes или no
                                confirmation_id = parts[3]  # ID подтверждения
                                
                                # Обрабатываем callback
                                confirmation_data = await smart_bot_trigger.handle_confirmation_callback(confirmation_id, answer)
                                
                                if answer == "yes" and confirmation_data:
                                    # Пользователь подтвердил - обрабатываем триггер
                                    response = await smart_bot_trigger.process_confirmed_trigger(
                                        confirmation_data['chat_id'],
                                        confirmation_data['message_text'],
                                        confirmation_data['user_id'],
                                        confirmation_data['is_quote'],
                                        confirmation_data['quoted_message_id']
                                    )
                                    
                                    if response:
                                        from api.telegram_core import send_telegram_message
                                        await send_telegram_message(
                                            confirmation_data['chat_id'], 
                                            response, 
                                            save_dialogue=True, 
                                            user_message=confirmation_data['message_text'], 
                                            user_id=confirmation_data['user_id']
                                        )
                                
                                # Отвечаем на callback
                                await answer_callback_query(callback_query["id"], "✅ Обработано" if answer == "yes" else "❌ Отменено")
                                
                        except Exception as e:
                            logger.error(f"❌ Ошибка обработки callback кнопок бота: {e}")
                            await answer_callback_query(callback_query["id"], f"❌ Ошибка: {str(e)[:50]}")
                        continue
                    
# Обработка удаления чанков памяти
                    if callback_data.startswith("delete_chunk_"):
                        try:
                            await handle_chunk_deletion(callback_query, callback_data, chat_id, message_id)
                        except Exception as e:
                            logger.error(f"Ошибка обработки удаления чанка: {e}")
                            await answer_callback_query(callback_query["id"], f"❌ Ошибка: {str(e)[:50]}")
                        continue
                    
                    # Обработка просмотра чанков памяти
                    if callback_data.startswith("view_chunk_"):
                        try:
                            await handle_chunk_view(callback_query, callback_data, chat_id, message_id)
                        except Exception as e:
                            logger.error(f"Ошибка обработки просмотра чанка: {e}")
                            await answer_callback_query(callback_query["id"], f"❌ Ошибка: {str(e)[:50]}")
                        continue
                    # Обработка фото-кнопок
                    if callback_data.startswith("photo_yes_"):
                        orig_message_id = callback_data.replace("photo_yes_", "")
                        await answer_callback_query(callback_query["id"], "Запускаю распознавание фото!")
                        # Достаём сообщение из БД
                        photo_message = sqlite_storage.get_pending_photo(chat_id, int(orig_message_id))
                        if photo_message:
                            try:
                                await process_telegram_photo_with_crypto_detection(photo_message, chat_id, user_id, temp_dir, download_telegram_file, send_telegram_message)
                                sqlite_storage.delete_pending_photo(chat_id, int(orig_message_id))
                            except Exception as e:
                                logger.error(f"Ошибка при обработке фото: {e}")
                                await send_telegram_message(chat_id, "❌ Ошибка при анализе изображения")
                        else:
                            await send_telegram_message(chat_id, "⚠️ Сообщение с фото не найдено или устарело")
                        continue
                    elif callback_data.startswith("photo_no_"):
                        await answer_callback_query(callback_query["id"], "Ок, не анализирую фото.")
                        continue
                    continue
                
                # Обработка сообщений из каналов
                if "channel_post" in update:
                    channel_post = update["channel_post"]
                    chat_id = str(channel_post["chat"]["id"])
                    chat_title = channel_post["chat"].get("title", "Неизвестный канал")
                    logger.info(f"🔥🔥🔥 [КАНАЛ {chat_id}] НАЙДЕН КАНАЛ: '{chat_title}' 🔥🔥🔥")
                    logger.info(f"[КАНАЛ {chat_id}] Полная информация: {channel_post}")
                    continue
                
                if "message" in update:
                    message = update["message"]
                    chat_id = str(message["chat"]["id"])
                    chat_type = message["chat"].get("type", "private")
                    user_id = f"tg_{chat_id}"
                    
                    # === ПРИВАТНЫЕ ЧАТЫ ===
                    if chat_type == "private":
                        from backend.api.telegram_private import handle_private_chat
                        await handle_private_chat(message, chat_id, user_id)
                        continue
                    
                    # === ГРУППОВОЙ ЧАТ ===
                    if chat_type in ("group", "supergroup"):
                        # Логируем все входящие сообщения из группы
                        logger.info(f"[ГРУППА {chat_id}] Входящее сообщение: {message}")
                        # Фильтрация: если сообщение от самого бота — игнорируем для триггера и анализа
                        from_user = message.get("from", {})
                        from_user_id = from_user.get("id")
                        if bot_id and str(from_user_id) == str(bot_id):
                            continue  # Не реагируем на свои сообщения
                        # 1. Приветствие при добавлении бота в группу
                        if "new_chat_members" in message:
                            for member in message["new_chat_members"]:
                                if bot_id and str(member.get("id")) == str(bot_id):
                                    await send_telegram_message(
                                        chat_id,
                                        "Ребята, я бот, созданный Игорем. Для назначения имён участников используйте команду /names."
                                    )
                                    logger.info(f"[ГРУППА {chat_id}] Бот добавлен в группу.")
                                    break
                        # 2. Режим ручного сбора имён
                        if "text" in message:
                            text = message["text"].strip()
                            # === КОМАНДА /init ===
                            if text == "/init" and group_names_mode.get(chat_id) == 'active':
                                await send_telegram_message(chat_id, "Инициализирую анализ всей истории группы...", None)
                                result = await analyze_group_history(chat_id, reason='init')
                                if result and isinstance(result, str):
                                    await send_telegram_message(chat_id, result, None)
                                logger.info(f"[ГРУППА {chat_id}] Запрошен полный анализ всей истории по команде /init.")
                                continue
                            # --- Автоматический переход в режим active, если имена уже назначены ---
                            if group_names_mode.get(chat_id) != 'active':
                                # Получаем все user_id из таблицы имён
                                try:
                                    conn = sqlite3.connect(sqlite_storage.db_path)
                                    cursor = conn.cursor()
                                    cursor.execute('SELECT user_id FROM group_user_names WHERE chat_id = ?', (chat_id,))
                                    user_ids = [row[0] for row in cursor.fetchall()]
                                    conn.close()
                                except Exception as e:
                                    logger.error(f"Ошибка при получении имён участников: {e}")
                                    user_ids = []
                                named_count = len(user_ids)
                                if named_count >= 1:
                                    group_names_mode[chat_id] = 'active'
                                    logger.info(f"[ГРУППА {chat_id}] Автоматически выставлен режим 'active' (найдено имён: {named_count})")
                                    # УБРАН автозапуск анализа истории при старте
                            # Включение режима сбора имён
                            if text == "/names":
                                group_names_mode[chat_id] = 'collecting'
                                await send_telegram_message(
                                    chat_id,
                                    "Ок, кого как зовут? Напишите в формате: @username Имя (или @user_id Имя)",
                                    None
                                )
                                logger.info(f"[ГРУППА {chat_id}] Включён режим сбора имён.")
                                continue
                            # Завершение сбора имён
                            if text == "/namesdone":
                                group_names_mode[chat_id] = 'active'
                                await send_telegram_message(
                                    chat_id,
                                    "Спасибо! Теперь я могу работать с группой.",
                                    None
                                )
                                logger.info(f"[ГРУППА {chat_id}] Режим сбора имён завершён.")
                                # Сразу запускаем анализ группы и создание души
                                await analyze_group_history(chat_id, reason='создание души')
                                continue
                            # Явный запуск оценки ситуации
                            if text == "/analyze" and group_names_mode.get(chat_id) == 'active':
                                await send_telegram_message(chat_id, "Анализирую ситуацию в группе...", None)
                                result = await analyze_group_history(chat_id, reason='ручной вызов')
                                if result and isinstance(result, str):
                                    await send_telegram_message(chat_id, result, None)
                                logger.info(f"[ГРУППА {chat_id}] Запрошен анализ ситуации по команде /analyze.")
                                continue
                            
                            # Отчет об эволюции системы
                            if text == "/ЭВОЛЮЦИЯ" or text == "/эволюция":
                                logger.info(f"[ГРУППА {chat_id}] Запрошен отчет об эволюции системы")
                                await send_evolution_report(chat_id)
                                continue
                            
                            # НЕЙРОСУД - многоэтапный анализ с разными AI моделями
                            if "НЕЙРОСУД" in text.upper() and group_names_mode.get(chat_id) == 'active':
                                logger.info(f"[ГРУППА {chat_id}] Запуск НЕЙРОСУДА по команде: {text}")
                                await neurosud_analysis(chat_id)
                                continue
                            
                            # Команда ЧАНКИ - показ коллективной памяти
                            if (text == "/ЧАНКИ" or text == "/чанки") and group_names_mode.get(chat_id) == 'active':
                                logger.info(f"[ГРУППА {chat_id}] Запрос на показ коллективной памяти по команде: {text}")
                                await show_collective_memory(chat_id)
                                continue
                            
                            # Команда ЧАНКИ_ПОЛНЫЕ - полный просмотр с кнопками удаления
                            if (text == "/ЧАНКИ_ПОЛНЫЕ" or text == "/чанки_полные") and group_names_mode.get(chat_id) == 'active':
                                logger.info(f"[ГРУППА {chat_id}] Запрос на полный просмотр чанков по команде: {text}")
                                await show_full_chunks_with_buttons(chat_id)
                                continue
                            # Если режим активен, ищем @user
                            if group_names_mode.get(chat_id) == 'collecting':
                                match = re.match(r"@(\w+|\d+)\s+(.+)", text)
                                if match:
                                    mention, name = match.groups()
                                    # Определяем user_id по username или числу
                                    target_user_id = None
                                    # Если это user_id (число)
                                    if mention.isdigit():
                                        target_user_id = mention
                                    else:
                                        # Поиск user_id по username среди последних сообщений группы
                                        group_msgs = sqlite_storage.get_group_messages(chat_id)
                                        for msg in reversed(group_msgs):
                                            u = msg.get("user_id", "")
                                            uname = msg.get("username", "")
                                            if uname == mention or (msg.get("from_username") == mention):
                                                target_user_id = u
                                                break
                                        if not target_user_id and "entities" in message:
                                            for ent in message["entities"]:
                                                if ent.get("type") == "mention":
                                                    if text[ent["offset"]+1:ent["offset"]+ent["length"]] == mention:
                                                        target_user_id = from_user_id
                                                        break
                                    if not target_user_id:
                                        await send_telegram_message(chat_id, f"Не удалось определить пользователя по @{mention}")
                                    else:
                                        sqlite_storage.set_group_user_name(chat_id, target_user_id, name.strip())
                                        await send_telegram_message(chat_id, f"Ок, его зовут {name.strip()}", None)
                                        logger.info(f"[ГРУППА {chat_id}] Назначено имя участнику {target_user_id}: {name.strip()}")
                                else:
                                    await send_telegram_message(chat_id, "Формат: @username Имя", None)
                                continue
                            # Если режим сбора имён активен, игнорируем остальные сообщения
                            if group_names_mode.get(chat_id) == 'active':
                                continue
                        # Сохраняем текстовые сообщения
                        if "text" in message:
                            message_text = message["text"]
                            from_user = message.get("from", {}).get("id", "")
                            message_id = message.get("message_id", 0)
                            ts = message.get("date", int(datetime.now().timestamp()))
                            sqlite_storage.save_group_message(
                                chat_id=chat_id,
                                message_id=message_id,
                                user_id=str(from_user),
                                msg_type="text",
                                content=message_text,
                                timestamp=ts
                            )


                            
                            # Проверяем цитирование бота
                            is_quote = False
                            quoted_message_id = None
                            if "reply_to_message" in message:
                                reply_to_message = message["reply_to_message"]
                                if reply_to_message.get("from", {}).get("is_bot", False):
                                    is_quote = True
                                    quoted_message_id = reply_to_message.get("message_id")
                                    logger.info(f"🔗 Обнаружено цитирование бота: {quoted_message_id}")
                            
                            # Триггер "бот"/обращение к Икар Икарыч
                            logger.info(f"[ГРУППА {chat_id}] Проверяем триггер Икар Икарыч | quote={is_quote} | text='{message_text[:80]}'")
                            from .group_bot_integration import check_and_handle_bot_trigger
                            bot_triggered = await check_and_handle_bot_trigger(chat_id, message_text, str(from_user), is_quote, quoted_message_id)
                            logger.info(f"[ГРУППА {chat_id}] Результат триггера: {bot_triggered}")
                            if bot_triggered:
                                continue
                            
                            # Триггер "ПАМЯТЬ" - экспорт всех чанков памяти группы
                            from .group_bot_integration import check_and_handle_memory_export_trigger
                            memory_export_triggered = await check_and_handle_memory_export_trigger(chat_id, message_text, str(from_user))
                            if memory_export_triggered:
                                continue
                            
                            # Новый триггер: если есть 'картинка:' (без учёта регистра)
                            from .group_image_trigger import group_image_trigger
                            from .telegram_core import send_telegram_photo
                            image_triggered = await group_image_trigger.try_trigger(chat_id, message_text, send_telegram_photo)
                            if image_triggered:
                                continue
                        # Обработка фотографий в группе - автоматическое распознавание + кнопки
                        elif "photo" in message:
                            logger.info(f"[ГРУППА {chat_id}] Получено фото - автоматическое распознавание + кнопки")
                            from_user = message.get("from", {}).get("id", "")
                            message_id = message.get("message_id", 0)
                            ts = message.get("date", int(datetime.now().timestamp()))
                            
                            # Сохраняем запись о фото
                            sqlite_storage.save_group_message(
                                chat_id=chat_id,
                                message_id=message_id,
                                user_id=str(from_user),
                                msg_type="photo",
                                content="[photo]",
                                timestamp=ts
                            )
                            logger.info(f"[DEBUG] save_pending_photo: chat_id={chat_id}, message_id={message_id}, user_id={from_user}, timestamp={ts}")
                            sqlite_storage.save_pending_photo(
                                chat_id=chat_id,
                                message_id=message_id,
                                user_id=str(from_user),
                                message_dict=message,
                                timestamp=ts
                            )
                            
                            # Автоматическое распознавание изображения (аналогично голосовым)
                            try:
                                from .auto_image_recognition import process_image_automatically
                                await process_image_automatically(chat_id, message, download_telegram_file, send_telegram_message)
                                logger.info(f"🤖 Автоматическое распознавание изображения запущено для {chat_id}_{message_id}")
                            except Exception as e:
                                logger.error(f"❌ Ошибка автоматического распознавания: {e}")
                            
                            # Также показываем кнопки для дополнительных действий
                            await send_photo_recognition_buttons(chat_id, message_id)
                            continue
                        # Сохраняем голосовые сообщения (с распознаванием)
                        elif "voice" in message:
                            voice = message["voice"]
                            file_id = voice["file_id"]
                            duration = voice.get("duration", 0)
                            from_user = message.get("from", {}).get("id", "")
                            message_id = message.get("message_id", 0)
                            ts = message.get("date", int(datetime.now().timestamp()))
                            audio_path = await download_telegram_file(file_id)
                            recognized_text = None
                            if audio_path:
                                try:
                                    stt = get_stt_engine()
                                    recognized_text = await stt.process_voice_message(audio_path)
                                except Exception as e:
                                    logger.error(f"Ошибка STT для группы: {e}")
                                try:
                                    os.remove(audio_path)
                                except:
                                    pass
                            sqlite_storage.save_group_message(
                                chat_id=chat_id,
                                message_id=message_id,
                                user_id=str(from_user),
                                msg_type="voice",
                                content=recognized_text or "[voice]",
                                timestamp=ts
                            )
                            # После распознавания прогоняем через тот же смарт-триггер, что и текст
                            if recognized_text:
                                try:
                                    from .group_bot_integration import check_and_handle_bot_trigger
                                    logger.info(f"[ГРУППА {chat_id}] Проверяем триггер Икар Икарыч (VOICE) | text='{recognized_text[:80]}'")
                                    bot_triggered = await check_and_handle_bot_trigger(chat_id, recognized_text, str(from_user), False, None)
                                    logger.info(f"[ГРУППА {chat_id}] Результат триггера (VOICE): {bot_triggered}")
                                    if bot_triggered:
                                        continue
                                except Exception as e:
                                    logger.error(f"❌ Ошибка триггера для голосового: {e}")
                        continue  # Не отвечаем в группу мгновенно
                    # === КОНЕЦ ГРУППОВОГО ЧАТА ===

                    # === КОНЕЦ ГРУППОВОГО ЧАТА ===
            
            await asyncio.sleep(1)  # Небольшая пауза между запросами
            
        except Exception as e:
            logger.error(f"Ошибка в Telegram polling: {e}")
            await asyncio.sleep(5)  # Пауза при ошибке

async def start_telegram_polling():
    """Запуск Telegram polling."""
    await telegram_polling()