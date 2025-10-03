import logging
import json
import asyncio
from backend.api.telegram_core import send_telegram_message_with_buttons, send_telegram_message, delete_telegram_message
from api.telegram_vision import get_image_analyzer
from backend.memory.sqlite import sqlite_storage

logger = logging.getLogger("chatumba.telegram.photo_handler")

async def send_photo_recognition_buttons(chat_id, message_id):
    """Отправляет две кнопки для распознавания фото: как изображение и как текст."""
    buttons = [
        [{"text": "Распознать как изображение", "callback_data": f"photo_img_{message_id}"}],
        [{"text": "Распознать как текст", "callback_data": f"photo_text_{message_id}"}]
    ]
    sent_msg_id = await send_telegram_message_with_buttons(
        chat_id,
        "Что сделать с этим фото?",
        buttons
    )
    # Планируем авто-удаление подсказки через 10 секунд
    if isinstance(sent_msg_id, int):
        async def _auto_delete():
            try:
                await asyncio.sleep(10)
                await delete_telegram_message(chat_id, sent_msg_id)
            except Exception:
                # Тихо игнорируем любые ошибки удаления
                pass
        asyncio.create_task(_auto_delete())

async def handle_photo_callback(callback_query, callback_data, chat_id, message_id, user_id, temp_dir, download_telegram_file):
    """
    Обрабатывает callback-кнопки для фото: как изображение и как текст.
    message_id должен браться только из callback_data (photo_img_12345), а не из callback_query['message']['message_id']!
    """
    # Получаем message_id из callback_data (например, photo_text_10996)
    if callback_data.startswith("photo_img_"):
        real_message_id = int(callback_data.replace("photo_img_", ""))
        from api.telegram_crypto_processing import process_telegram_photo_with_crypto_detection
        logger.info(f"[DEBUG] get_pending_photo: chat_id={chat_id}, message_id={real_message_id}")
        photo_message = sqlite_storage.get_pending_photo(chat_id, real_message_id)
        logger.info(f"[DEBUG] get_pending_photo result: {'FOUND' if photo_message else 'NOT FOUND'}")
        if photo_message:
            await send_telegram_message(chat_id, "🔍 Анализирую изображение...", None)
            await process_telegram_photo_with_crypto_detection(photo_message, chat_id, user_id, temp_dir, download_telegram_file, send_telegram_message)
            sqlite_storage.delete_pending_photo(chat_id, real_message_id)
        else:
            await send_telegram_message(chat_id, "⚠️ Сообщение с фото не найдено или устарело")
        return True
    elif callback_data.startswith("photo_text_"):
        real_message_id = int(callback_data.replace("photo_text_", ""))
        logger.info(f"[DEBUG] get_pending_photo: chat_id={chat_id}, message_id={real_message_id}")
        photo_message = sqlite_storage.get_pending_photo(chat_id, real_message_id)
        logger.info(f"[DEBUG] get_pending_photo result: {'FOUND' if photo_message else 'NOT FOUND'}")
        if photo_message:
            photos = photo_message.get("photo", [])
            if not photos:
                await send_telegram_message(chat_id, "❌ Не удалось найти фото для распознавания текста.")
                return True
            photo = photos[-1]
            file_id = photo.get("file_id")
            if not file_id:
                await send_telegram_message(chat_id, "❌ Не удалось получить file_id фото.")
                return True
            local_path = await download_telegram_file(file_id)
            if not local_path:
                await send_telegram_message(chat_id, "❌ Не удалось скачать фото для распознавания текста.")
                return True
            analyzer = get_image_analyzer()
            prompt = "Найди и выпиши весь текст, который есть на этом изображении. Ответь строго в формате JSON: {\"text\": \"...\"}"
            result = await analyzer.analyze_image(local_path, prompt)
            text = None
            if result:
                try:
                    # Используем крутой парсер из utils/robust_json_parser.py
                    from utils.robust_json_parser import robust_json_parser

                    # Предварительная обработка ответа модели
                    processed_result = result.strip()

                    # Если ответ начинается с "Успешно проанализировано", ищем JSON после этого
                    if processed_result.startswith("Успешно проанализировано"):
                        # Ищем начало JSON (```json или {)
                        json_start = processed_result.find("```json")
                        if json_start == -1:
                            json_start = processed_result.find("{")
                        if json_start != -1:
                            processed_result = processed_result[json_start:]

                    # СУПЕР ПРОСТОЙ ПОДХОД: игнорируем JSON, берем весь текст между первой и последней кавычкой
                    if '"text":' in processed_result:
                        # Логируем полный ответ для отладки
                        logger.info(f"[PHOTO TEXT] ПОЛНЫЙ ОТВЕТ МОДЕЛИ: {processed_result[:500]}...")

                        # Ищем первую кавычку после "text":
                        text_pos = processed_result.find('"text":')
                        if text_pos != -1:
                            # Ищем открывающую кавычку после "text":
                            start_quote = processed_result.find('"', text_pos + 7)
                            if start_quote != -1:
                                # Берем ВЕСЬ текст от открывающей кавычки до КОНЦА ответа
                                # Это гарантирует, что мы возьмем весь текст, даже если там есть кавычки
                                raw_text = processed_result[start_quote + 1:].strip()

                                # Если текст заканчивается кавычкой - убираем ее
                                if raw_text.endswith('"'):
                                    raw_text = raw_text[:-1]

                                # Обрабатываем escaped символы
                                text = raw_text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')

                                # Убираем возможные завершающие символы (}, ``` и т.д.)
                                text = text.split('}')[0].split('```')[0].strip()

                                logger.info(f"[PHOTO TEXT] СУПЕР ПРОСТОЙ ПАРСИНГ СРАБОТАЛ! Найден текст длиной {len(text)} символов")
                                logger.info(f"[PHOTO TEXT] Первые 300 символов: {text[:300]}...")

                                if text.strip():
                                    await send_telegram_message(chat_id, f"📝 <b>Распознанный текст:</b>\n\n{text}", "HTML")
                                    return True

                    # Парсим обработанный ответ от модели
                    json_objects = robust_json_parser(processed_result)

                    # Ищем объект с ключом "text"
                    for obj in json_objects:
                        if isinstance(obj, dict) and "text" in obj:
                            text = obj["text"].strip()
                            logger.info(f"[PHOTO TEXT] Найден текст в JSON: {text[:100]}...")
                            break

                    # Логируем найденные JSON объекты для отладки
                    if not text:
                        logger.info(f"[PHOTO TEXT] JSON объекты найдены: {len(json_objects)}")
                        for i, obj in enumerate(json_objects[:3]):  # Логируем первые 3 объекта
                            logger.info(f"[PHOTO TEXT] Объект {i}: {obj}")
                        logger.info(f"[PHOTO TEXT] Обработанный ответ: {processed_result[:300]}...")

                        # Пытаемся напрямую распарсить JSON стандартными средствами
                        try:
                            import json
                            # Простая попытка распарсить как обычный JSON
                            if processed_result.strip().startswith('{'):
                                direct_json = json.loads(processed_result.strip())
                                if isinstance(direct_json, dict) and "text" in direct_json:
                                    text = direct_json["text"].strip()
                                    logger.info(f"[PHOTO TEXT] Прямой парсинг сработал! Найден текст: {text[:100]}...")
                        except Exception as e:
                            logger.error(f"[PHOTO TEXT] Прямой парсинг тоже не сработал: {e}")

                        # Fallback: если все провалилось, но есть полезный текст в processed_result
                        if not text and len(processed_result.strip()) > 50:
                            # Ищем текст между кавычками после "text": (улучшенный regex)
                            import re
                            # Более надежный паттерн для захвата всего текста, включая многострочный
                            text_match = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', processed_result, re.DOTALL)
                            if text_match:
                                text = text_match.group(1).strip()
                                # Обрабатываем escaped символы
                                text = text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                                logger.info(f"[PHOTO TEXT] Regex fallback сработал! Найден текст длиной {len(text)} символов: {text[:100]}...")
                            else:
                                logger.error(f"[PHOTO TEXT] Regex fallback не сработал")

                            # Дополнительный fallback: если regex не сработал, попробуем найти весь контент между кавычками
                            if not text:
                                # Ищем все между первой и последней кавычкой после "text":
                                text_start = processed_result.find('"text": "')
                                if text_start != -1:
                                    text_start += 9  # Пропускаем '"text": "'
                                    # Ищем последнюю кавычку в строке
                                    text_end = processed_result.rfind('"', text_start)
                                    if text_end != -1:
                                        raw_text = processed_result[text_start:text_end]
                                        # Обрабатываем escaped символы
                                        text = raw_text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                                        logger.info(f"[PHOTO TEXT] Raw fallback сработал! Найден текст длиной {len(text)} символов: {text[:100]}...")
                                    else:
                                        logger.error(f"[PHOTO TEXT] Все методы парсинга провалились!")

                    # Fallback: если JSON не найден, но есть текст от локального анализа
                    if not text and result.strip():
                        # Проверяем, является ли ответ результатом локального анализа
                        if "[Локальный анализ]" in result:
                            # Убираем префикс и используем остальной текст
                            text = result.replace("[Локальный анализ]", "").strip()
                        elif len(result.strip()) > 10:  # Если есть значительный текст
                            # Пытаемся извлечь текст из markdown или простого ответа
                            import re
                            # Убираем markdown разметку
                            clean_text = re.sub(r'```json\s*', '', result)
                            clean_text = re.sub(r'```\s*', '', clean_text)
                            clean_text = clean_text.strip()
                            if clean_text and not clean_text.startswith('{'):
                                text = clean_text

                except Exception as e:
                    logger.error(f"[PHOTO TEXT] Ошибка парсинга JSON: {e}. Ответ модели: {result[:200]}...")
                    # Даже при ошибке парсинга, пытаемся извлечь полезный текст
                    if "[Локальный анализ]" in result:
                        text = result.replace("[Локальный анализ]", "").strip()
            if text:
                await send_telegram_message(chat_id, f"📝 <b>Распознанный текст:</b>\n\n{text}", "HTML")
            else:
                await send_telegram_message(chat_id, "❌ Не удалось корректно распознать текст на изображении.")
            import os
            try:
                os.remove(local_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")
            sqlite_storage.delete_pending_photo(chat_id, real_message_id)
        else:
            await send_telegram_message(chat_id, "⚠️ Сообщение с фото не найдено или устарело")
        return True
    return False 