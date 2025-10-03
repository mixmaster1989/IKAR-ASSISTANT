import time
import logging
import re
import asyncio
import tempfile
import os
from pathlib import Path
from backend.memory.sqlite import sqlite_storage
from backend.vision.image_generator import image_generator, translate_prompt_to_english

logger = logging.getLogger("chatumba.group_image_trigger")

# Словарь для хранения времени последнего срабатывания по chat_id
last_image_trigger_time = {}

class GroupImageTrigger:
    def __init__(self):
        self.cooldown_sec = 120  # 2 минуты cooldown для генерации изображений
        self.trigger_word = "картинка:"
        
    async def try_trigger(self, chat_id: str, message_text: str, send_telegram_photo):
        """
        Проверяет триггер и генерирует изображение если нужно.
        
        Args:
            chat_id: ID чата
            message_text: Текст сообщения
            send_telegram_photo: Функция отправки фото в Telegram
            
        Returns:
            bool: True если триггер сработал, False если нет
        """
        
        # Проверка триггера ("ботнарисуй" в любом регистре)
        if self.trigger_word not in message_text.lower():
            return False
            
        # Проверка cooldown
        now = time.time()
        last_time = last_image_trigger_time.get(chat_id, 0)
        if now - last_time < self.cooldown_sec:
            logger.info(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Cooldown для чата {chat_id}, не реагируем.")
            return True  # Уже сработал недавно, не реагируем
        
        last_image_trigger_time[chat_id] = now
        logger.info(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Сработал триггер по слову '{self.trigger_word}' в чате {chat_id}")
        
        # Извлекаем промпт из сообщения
        prompt = self._extract_prompt(message_text)
        
        if not prompt:
            # Если промпт не найден, отправляем инструкцию
            await self._send_instruction_message(chat_id, send_telegram_photo)
            return True
            
        logger.info(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Извлечен промпт: '{prompt}'")
        
        # Генерируем изображение
        await self._generate_and_send_image(chat_id, prompt, send_telegram_photo)
        
        return True
    
    def _extract_prompt(self, message_text: str) -> str:
        """
        Извлекает промпт из сообщения.
        
        Поддерживает форматы:
        - "картинка: кот на крыше"
        - "КАРТИНКА: кот на крыше"
        - "Эй, картинка: красивый закат"
        
        Args:
            message_text: Текст сообщения
            
        Returns:
            str: Извлеченный промпт или пустая строка
        """
        
        # Ищем слово "картинка:" и всё что после него
        pattern = r'картинка:\s*(.+?)(?:\s*$|[.!?])'
        match = re.search(pattern, message_text.lower())
        
        if match:
            prompt = match.group(1).strip()
            # Убираем лишние символы в конце
            prompt = re.sub(r'[.!?]*$', '', prompt).strip()
            return prompt
        
        return ""
    
    async def _send_instruction_message(self, chat_id: str, send_telegram_photo):
        """
        Отправляет инструкцию по использованию триггера.
        
        Args:
            chat_id: ID чата
            send_telegram_photo: Функция отправки фото в Telegram
        """
        instruction = (
            "🎨 Для генерации изображения используйте формат:\n"
            "**картинка:** [описание изображения]\n\n"
            "Например:\n"
            "• картинка: кот на крыше\n"
            "• картинка: красивый закат над океаном\n"
            "• картинка: киберпанк город\n\n"
            "⏳ Генерация может занять 1-5 минут"
        )
        
        # Отправляем как текстовое сообщение через send_telegram_message
        try:
            # Импортируем функцию отправки текста
            from api.telegram_core import send_telegram_message
            await send_telegram_message(chat_id, instruction)
        except Exception as e:
            logger.error(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Ошибка отправки инструкции: {e}")
    
    async def _generate_and_send_image(self, chat_id: str, prompt: str, send_telegram_photo):
        """
        Генерирует и отправляет изображение.
        
        Args:
            chat_id: ID чата
            prompt: Промпт для генерации
            send_telegram_photo: Функция отправки фото в Telegram
        """
        
        try:
            # Отправляем уведомление о начале генерации
            from api.telegram_core import send_telegram_message
            await send_telegram_message(
                chat_id, 
                f"🎨 Генерирую изображение...\n⏳ Это может занять 1-5 минут..."
            )
            
            # Переводим промпт на английский
            english_prompt = await translate_prompt_to_english(prompt)
            logger.info(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Переведенный промпт: '{english_prompt}'")
            
            # Генерируем изображение
            logger.info(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Запуск генерации изображения...")
            
            image_bytes = await image_generator(
                prompt=english_prompt,
                model="text2img",  # Используем основную модель DeepAI
                width=512,
                height=512,
                timeout=300  # 5 минут таймаут для DeepAI
            )
            
            if not image_bytes:
                logger.error(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Не удалось сгенерировать изображение")
                await send_telegram_message(
                    chat_id, 
                    f"❌ Не удалось сгенерировать изображение для: '{prompt}'\n"
                    "Возможно, сервис перегружен. Попробуйте позже."
                )
                return
            
            # Сохраняем изображение во временный файл
            temp_dir = Path(tempfile.gettempdir()) / "chatumba_images"
            temp_dir.mkdir(exist_ok=True)
            
            image_filename = f"generated_{chat_id}_{int(time.time())}.png"
            image_path = temp_dir / image_filename
            
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            
            logger.info(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Изображение сохранено: {image_path}")
            
            # Отправляем изображение в Telegram
            caption = f"🎨 Сгенерировано по запросу: '{prompt}'"
            await send_telegram_photo(chat_id, str(image_path), caption)
            
            logger.info(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Изображение отправлено в чат {chat_id}")
            
            # Удаляем временный файл через 10 минут
            asyncio.create_task(self._cleanup_temp_file(image_path, delay=600))
            
        except Exception as e:
            logger.error(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Ошибка при генерации изображения: {e}")
            try:
                from api.telegram_core import send_telegram_message
                await send_telegram_message(
                    chat_id, 
                    f"❌ Произошла ошибка при генерации изображения: {str(e)}\n"
                    "Попробуйте позже или обратитесь к администратору."
                )
            except:
                pass  # Если даже отправка ошибки не удалась
    
    async def _cleanup_temp_file(self, file_path: Path, delay: int = 600):
        """
        Удаляет временный файл через заданное время.
        
        Args:
            file_path: Путь к файлу
            delay: Задержка в секундах
        """
        await asyncio.sleep(delay)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Удален временный файл: {file_path}")
        except Exception as e:
            logger.warning(f"[ИЗОБРАЖЕНИЕ-ТРИГГЕР] Не удалось удалить временный файл {file_path}: {e}")

# Экземпляр для импорта
group_image_trigger = GroupImageTrigger() 