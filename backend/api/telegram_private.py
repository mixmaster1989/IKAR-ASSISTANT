"""
Модуль для обработки приватных чатов с авторизацией
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from backend.api.telegram_auth import telegram_auth
from backend.api.telegram_core import (
    process_telegram_message, send_telegram_message, 
    send_monitoring_report, send_autonomous_message,
    send_autonomous_channel_message, send_channel_startup_message,
    download_telegram_file, get_stt_engine, get_tts_engine,
    temp_dir, TELEGRAM_CONFIG, monitoring_chat_id
)
from backend.api.telegram_polling import (
    send_evolution_report, show_collective_memory, 
    show_full_chunks_with_buttons, process_telegram_photo_with_crypto_detection
)
from backend.api.telegram_photo_handler import send_photo_recognition_buttons
from backend.memory.sqlite import sqlite_storage

logger = logging.getLogger(__name__)

async def handle_private_chat(message: Dict[str, Any], chat_id: str, user_id: str):
    """
    Обрабатывает сообщения в приватных чатах с авторизацией
    """
    global monitoring_chat_id
    
    try:
        # Получаем информацию о пользователе
        from_user = message.get("from", {})
        username = from_user.get("username")
        first_name = from_user.get("first_name")
        last_name = from_user.get("last_name")
        
        # Проверяем авторизацию
        if not telegram_auth.is_user_authorized(user_id):
            # Пользователь не авторизован - проверяем секретное слово
            if "text" in message:
                text = message["text"].strip()
                auth_result = telegram_auth.process_auth_attempt(
                    user_id, text, username, first_name, last_name
                )
                
                # Отправляем результат авторизации
                await send_telegram_message(chat_id, auth_result["message"])
                
                # Если авторизация успешна, продолжаем обработку
                if auth_result["authorized"]:
                    # Устанавливаем chat_id для мониторинга (первый авторизованный пользователь)
                    if monitoring_chat_id is None:
                        monitoring_chat_id = chat_id
                        logger.info(f"📊 Установлен мониторинг чат: {chat_id}")
                        await send_telegram_message(chat_id, "📊 **МОНИТОРИНГ АКТИВИРОВАН**\nБуду присылать отчеты раз в день\n💭 **АВТОНОМНЫЕ СООБЩЕНИЯ ВКЛЮЧЕНЫ**\nБуду писать сам каждый час!")
                else:
                    # Не авторизован - прекращаем обработку
                    return
            else:
                # Не текстовое сообщение от неавторизованного пользователя
                await send_telegram_message(chat_id, "🔐 Для использования бота введите секретное слово.")
                return
        else:
            # Пользователь авторизован - обновляем активность
            telegram_auth.update_last_activity(user_id)
            
            # Устанавливаем chat_id для мониторинга (первый авторизованный пользователь)
            if monitoring_chat_id is None:
                monitoring_chat_id = chat_id
                logger.info(f"📊 Установлен мониторинг чат: {chat_id}")
                await send_telegram_message(chat_id, "📊 **МОНИТОРИНГ АКТИВИРОВАН**\nБуду присылать отчеты раз в день\n💭 **АВТОНОМНЫЕ СООБЩЕНИЯ ВКЛЮЧЕНЫ**\nБуду писать сам каждый час!")
        
        # Обработка команд мониторинга
        if "text" in message:
            text = message["text"]
            
            if text == "/report":
                await send_monitoring_report()
                return
            elif text == "/monitor_on":
                monitoring_chat_id = chat_id
                await send_telegram_message(chat_id, "📊 Мониторинг включен для этого чата")
                return
            elif text == "/monitor_off":
                monitoring_chat_id = None
                await send_telegram_message(chat_id, "📊 Мониторинг отключен")
                return
            elif text == "/autonomous":
                await send_autonomous_message()
                return
            elif text == "/ЭВОЛЮЦИЯ" or text == "/эволюция":
                await send_evolution_report(chat_id)
                return
            elif text == "/channel_on":
                TELEGRAM_CONFIG["enable_channel_posting"] = True
                await send_telegram_message(chat_id, "📢 Постинг в канал включен")
                logger.info("Постинг в канал включен пользователем")
                return
            elif text == "/channel_off":
                TELEGRAM_CONFIG["enable_channel_posting"] = False
                await send_telegram_message(chat_id, "📢 Постинг в канал отключен")
                logger.info("Постинг в канал отключен пользователем")
                return
            elif text == "/channel_post":
                if TELEGRAM_CONFIG["enable_channel_posting"]:
                    await send_autonomous_channel_message()
                    await send_telegram_message(chat_id, "📢 Сообщение отправлено в канал")
                else:
                    await send_telegram_message(chat_id, "❌ Постинг в канал отключен. Используйте /channel_on")
                return
            elif text == "/channel_startup":
                logger.info(f"🎯 Получена команда /channel_startup от пользователя {chat_id}")
                
                if TELEGRAM_CONFIG["enable_channel_posting"]:
                    logger.info("✅ Постинг в канал включен, вызываем send_channel_startup_message...")
                    success = await send_channel_startup_message()
                    logger.info(f"📊 Результат send_channel_startup_message: {success}")
                    
                    if success:
                        await send_telegram_message(chat_id, "📢 Стартовое сообщение отправлено в канал 36,6°")
                        logger.info("✅ Команда /channel_startup выполнена успешно")
                    else:
                        await send_telegram_message(chat_id, "❌ Не удалось отправить стартовое сообщение. Проверьте логи сервера.")
                        logger.error("❌ Команда /channel_startup завершилась с ошибкой")
                else:
                    await send_telegram_message(chat_id, "❌ Постинг в канал отключен. Используйте /channel_on")
                return
            elif text == "/auth_stats" or text == "/статистика_авторизации":
                # Статистика авторизации
                stats = telegram_auth.get_auth_stats()
                stats_text = "📊 **СТАТИСТИКА АВТОРИЗАЦИИ**\n\n"
                stats_text += f"👥 **Авторизованных пользователей:** {stats['authorized_users']}\n"
                stats_text += f"🚫 **Заблокированных пользователей:** {stats['banned_users']}\n"
                stats_text += f"🔢 **Попыток за 24 часа:** {stats['attempts_24h']}\n"
                await send_telegram_message(chat_id, stats_text, "HTML")
                return
            elif text == "/ЧАНКИ" or text == "/чанки":
                logger.info(f"🧠 Запрос на показ коллективной памяти от пользователя {chat_id}")
                await show_collective_memory(chat_id)
                return
            elif text == "/ЧАНКИ_ПОЛНЫЕ" or text == "/чанки_полные":
                logger.info(f"🧠 Запрос на полный просмотр чанков от пользователя {chat_id}")
                await show_full_chunks_with_buttons(chat_id)
                return
        
        # Обработка текстовых сообщений (ТОЛЬКО ДЛЯ АВТОРИЗОВАННЫХ)
        if "text" in message:
            message_text = message["text"]
            logger.info(f"📨 Получено сообщение от {chat_id}: {message_text}")
            
            # Проверяем авторизацию ПЕРЕД обработкой
            if telegram_auth.is_user_authorized(user_id):
                # Обрабатываем сообщение
                response_text, audio_path = await process_telegram_message(user_id, message_text)
                
                # Отправляем ответ
                await send_telegram_message(chat_id, response_text)
            else:
                # Пользователь не авторизован - отправляем сообщение об авторизации
                await send_telegram_message(chat_id, "🔐 Для общения со мной в личных сообщениях необходимо авторизоваться. Отправьте секретное слово.")
        
        # Обработка фотографий в приватных чатах - автоматическое распознавание + кнопки
        elif "photo" in message:
            logger.info(f"📷 Получено фото от {chat_id} - автоматическое распознавание + кнопки")
            from_user = message.get("from", {}).get("id", "")
            message_id = message.get("message_id", 0)
            ts = message.get("date", int(datetime.now().timestamp()))
            
            # Сохраняем запись о фото в БД
            sqlite_storage.save_group_message(
                chat_id=chat_id,
                message_id=message_id,
                user_id=str(from_user),
                msg_type="photo",
                content="[photo]",
                timestamp=ts
            )
            
            # Сохраняем фото для последующей обработки
            sqlite_storage.save_pending_photo(
                chat_id=chat_id,
                message_id=message_id,
                user_id=str(from_user),
                message_dict=message,
                timestamp=ts
            )
            
            # Автоматическое распознавание изображения (аналогично голосовым)
            try:
                from api.auto_image_recognition import process_image_automatically
                await process_image_automatically(chat_id, message, download_telegram_file, send_telegram_message)
                logger.info(f"🤖 Автоматическое распознавание изображения запущено для приватного чата {chat_id}_{message_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка автоматического распознавания в приватном чате: {e}")
            
            # Также показываем кнопки для дополнительных действий
            await send_photo_recognition_buttons(chat_id, message_id)
        
        # Обработка голосовых сообщений
        elif "voice" in message:
            voice = message["voice"]
            file_id = voice["file_id"]
            duration = voice.get("duration", 0)
            
            logger.info(f"🎤 Получено голосовое сообщение от {chat_id} (длительность: {duration}с)")
            
            # Скачиваем голосовое сообщение
            audio_path = await download_telegram_file(file_id)
            
            if audio_path:
                try:
                    # Распознаем речь
                    stt = get_stt_engine()
                    recognized_text = await stt.process_voice_message(audio_path)
                    
                    if recognized_text:
                        logger.info(f"🗣️ Распознано: {recognized_text}")
                        
                        # Обрабатываем как обычное сообщение с голосовым ответом
                        response_text, response_audio = await process_telegram_message(
                            user_id, recognized_text, use_voice_response=True
                        )
                        
                        # Отправляем текстовый ответ
                        await send_telegram_message(chat_id, f"🎤 Ты сказал: {recognized_text}\n\n{response_text}")
                        
                        # Отправляем голосовой ответ если есть
                        if response_audio and os.path.exists(response_audio):
                            from backend.api.telegram_core import send_telegram_voice
                            await send_telegram_voice(chat_id, response_audio)
                            # Удаляем временный файл ответа
                            try:
                                os.remove(response_audio)
                            except:
                                pass
                    else:
                        await send_telegram_message(chat_id, "Не смог разобрать что ты сказал 🤷‍♂️")
                    
                    # Удаляем временный файл входящего голоса
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                        
                except Exception as e:
                    logger.error(f"Ошибка обработки голоса: {e}")
                    await send_telegram_message(chat_id, "Ошибка при обработке голосового сообщения")
                    
                    # Удаляем временный файл при ошибке
                    try:
                        os.remove(audio_path)
                    except:
                        pass
            else:
                await send_telegram_message(chat_id, "Не удалось скачать голосовое сообщение")
                
    except Exception as e:
        logger.error(f"Ошибка обработки приватного чата: {e}")
        await send_telegram_message(chat_id, "❌ Произошла ошибка при обработке сообщения") 