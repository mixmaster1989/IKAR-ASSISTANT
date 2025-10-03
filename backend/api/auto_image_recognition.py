"""
🤖 Auto Image Recognition - Автоматическое распознавание всех изображений
Аналогично голосовым сообщениям, все изображения автоматически анализируются и сохраняются в историю
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger("chatumba.auto_image_recognition")

class AutoImageRecognition:
    """Автоматическое распознавание изображений с сохранением в историю"""
    
    def __init__(self):
        self.recognition_in_progress = set()  # Множество обрабатываемых изображений
        self.analyzer = None
        
    async def process_image_automatically(self, chat_id: str, message: Dict[str, Any], 
                                        download_telegram_file, send_telegram_message) -> bool:
        """
        Автоматически обрабатывает изображение и сохраняет описание в историю
        
        Args:
            chat_id: ID чата
            message: Сообщение с изображением
            download_telegram_file: Функция скачивания файлов
            send_telegram_message: Функция отправки сообщений
            
        Returns:
            bool: True если обработка начата, False если пропущено
        """
        try:
            # Получаем информацию об изображении
            photos = message.get("photo", [])
            if not photos:
                return False
                
            # Берем самую большую фотографию
            photo = photos[-1]
            file_id = photo.get("file_id")
            message_id = message.get("message_id", 0)
            
            if not file_id:
                return False
            
            # Создаем уникальный ключ для отслеживания
            processing_key = f"{chat_id}_{message_id}_{file_id}"
            
            # Проверяем, не обрабатывается ли уже это изображение
            if processing_key in self.recognition_in_progress:
                logger.debug(f"🔄 Изображение {processing_key} уже обрабатывается")
                return True
                
            # Добавляем в список обрабатываемых
            self.recognition_in_progress.add(processing_key)
            
            try:
                # Запускаем асинхронную обработку
                asyncio.create_task(self._process_image_async(
                    chat_id, message_id, file_id, message, 
                    download_telegram_file, send_telegram_message, processing_key
                ))
                
                logger.info(f"🤖 Автоматическое распознавание изображения запущено: {chat_id}_{message_id}")
                return True
                
            except Exception as e:
                # Убираем из списка обрабатываемых при ошибке
                self.recognition_in_progress.discard(processing_key)
                logger.error(f"❌ Ошибка запуска автоматического распознавания: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка в process_image_automatically: {e}")
            return False
    
    async def _process_image_async(self, chat_id: str, message_id: int, file_id: str, 
                                 message: Dict[str, Any], download_telegram_file, 
                                 send_telegram_message, processing_key: str):
        """
        Асинхронная обработка изображения
        """
        try:
            # Инициализируем анализатор если нужно
            if self.analyzer is None:
                from api.telegram_vision import get_image_analyzer
                self.analyzer = get_image_analyzer()
            
            # Скачиваем изображение
            local_path = await download_telegram_file(file_id)
            if not local_path:
                logger.error(f"❌ Не удалось скачать изображение: {file_id}")
                return
            
            # Определяем тип чата для выбора промпта
            chat_type = message.get("chat", {}).get("type", "private")
            if chat_type in ("group", "supergroup"):
                prompt = "Что на этом изображении? Опиши кратко и по делу. Используй русский язык."
            else:
                prompt = "Что на этом изображении? Опиши подробно, обращая внимание на детали. Используй русский язык."
            
            # Анализируем изображение
            logger.info(f"🔍 Анализирую изображение: {file_id}")
            description = await self.analyzer.analyze_image(local_path, prompt)
            
            if description:
                # Очищаем описание от префиксов
                clean_description = self._clean_description(description)
                
                # Сохраняем в историю как текстовое сообщение
                await self._save_image_description_to_history(
                    chat_id, message_id, clean_description, message
                )
                
                # Отправляем уведомление о распознавании (только в группы)
                if chat_type in ("group", "supergroup"):
                    await self._send_recognition_notification(
                        chat_id, clean_description, send_telegram_message
                    )
                
                logger.info(f"✅ Изображение распознано и сохранено: {chat_id}_{message_id}")
            else:
                logger.warning(f"⚠️ Не удалось распознать изображение: {file_id}")
            
            # Удаляем временный файл
            try:
                os.remove(local_path)
            except Exception as e:
                logger.error(f"❌ Ошибка удаления временного файла: {e}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка в _process_image_async: {e}")
        finally:
            # Убираем из списка обрабатываемых
            self.recognition_in_progress.discard(processing_key)
    
    def _clean_description(self, description: str) -> str:
        """Очищает описание от префиксов и лишнего текста"""
        try:
            # Убираем префиксы
            prefixes_to_remove = [
                "[Локальный анализ]",
                "Успешно проанализировано изображение:",
                "На изображении обнаружено:",
                "Я вижу на изображении:",
                "👁️",
                "**Я вижу на изображении:**"
            ]
            
            clean_desc = description
            for prefix in prefixes_to_remove:
                clean_desc = clean_desc.replace(prefix, "").strip()
            
            # Убираем лишние переносы строк
            clean_desc = "\n".join(line.strip() for line in clean_desc.split("\n") if line.strip())
            
            return clean_desc
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки описания: {e}")
            return description
    
    async def _save_image_description_to_history(self, chat_id: str, message_id: int, 
                                               description: str, original_message: Dict[str, Any]):
        """Сохраняет описание изображения в историю"""
        try:
            from memory.sqlite import sqlite_storage
            from datetime import datetime
            
            # Получаем информацию о пользователе
            from_user = original_message.get("from", {})
            user_id = str(from_user.get("id", ""))
            timestamp = original_message.get("date", int(datetime.now().timestamp()))
            
            # Формируем контент с описанием
            content = f"[Изображение] {description}"
            
            # Сохраняем в групповую историю
            sqlite_storage.save_group_message(
                chat_id=chat_id,
                message_id=message_id,
                user_id=user_id,
                msg_type="image_description",
                content=content,
                timestamp=timestamp
            )
            
            # Также сохраняем в новую систему памяти если доступна
            try:
                from memory.memory_integration import get_memory_integration
                integration = get_memory_integration()
                if integration.initialized:
                    integration.add_group_message(chat_id, user_id, content, timestamp)
                    logger.debug(f"💾 Описание изображения сохранено в новую систему памяти: {chat_id}")
            except Exception as e:
                logger.debug(f"⚠️ Не удалось сохранить в новую систему памяти: {e}")
            
            logger.info(f"💾 Описание изображения сохранено в историю: {chat_id}_{message_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения описания в историю: {e}")
    
    async def _send_recognition_notification(self, chat_id: str, description: str, 
                                           send_telegram_message):
        """Отправляет уведомление о распознавании в группу с автоудалением через 30 секунд"""
        try:
            notification = "🤖 Распознано изображение"
            
            # Отправляем уведомление и получаем message_id
            sent_msg_id = await send_telegram_message(chat_id, notification)
            
            # Планируем авто-удаление уведомления через 30 секунд
            if isinstance(sent_msg_id, int):
                async def _auto_delete_notification():
                    try:
                        await asyncio.sleep(30)  # 30 секунд задержка
                        from .telegram_core import delete_telegram_message
                        await delete_telegram_message(chat_id, sent_msg_id)
                        logger.debug(f"🧹 Уведомление о распознавании {sent_msg_id} удалено из чата {chat_id}")
                    except Exception as e:
                        # Тихо игнорируем любые ошибки удаления
                        logger.debug(f"⚠️ Не удалось удалить уведомление {sent_msg_id}: {e}")
                
                asyncio.create_task(_auto_delete_notification())
                logger.info(f"⏰ Запланировано автоудаление уведомления {sent_msg_id} через 30 секунд")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику обработки"""
        return {
            "processing_count": len(self.recognition_in_progress),
            "processing_keys": list(self.recognition_in_progress),
            "analyzer_initialized": self.analyzer is not None
        }

# Глобальный экземпляр
auto_image_recognition = AutoImageRecognition()

# Функция для удобного использования
async def process_image_automatically(chat_id: str, message: Dict[str, Any], 
                                    download_telegram_file, send_telegram_message) -> bool:
    """Удобная функция для автоматической обработки изображения"""
    return await auto_image_recognition.process_image_automatically(
        chat_id, message, download_telegram_file, send_telegram_message
    )




