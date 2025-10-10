"""
🧠 Smart Notifications - Умные уведомления о статусе ИИ
Показывает пользователю что Икар реально работает и думает
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("chatumba.smart_notifications")

class SmartNotifications:
    """Система умных уведомлений о статусе работы ИИ"""
    
    def __init__(self):
        self.notification_templates = {
            "thinking": [
                "🧠 Анализирую ваш запрос...",
                "💭 Думаю над лучшим ответом...",
                "🔍 Изучаю контекст разговора...",
                "⚡ Обрабатываю информацию...",
                "🎯 Формирую идеальный ответ..."
            ],
            "memory_search": [
                "📚 Ищу в памяти релевантную информацию...",
                "🔎 Анализирую предыдущие разговоры...",
                "💾 Обращаюсь к базе знаний...",
                "🧩 Собираю контекст из памяти...",
                "📖 Изучаю историю общения..."
            ],
            "generating_image": [
                "🎨 Создаю изображение для вас...",
                "🖼️ Генерирую визуальный контент...",
                "✨ Рисую картину по вашему запросу...",
                "🎭 Создаю художественное изображение...",
                "🌈 Генерирую красочную картинку..."
            ],
            "generating_voice": [
                "🎤 Создаю голосовое сообщение...",
                "🗣️ Озвучиваю текст для вас...",
                "🎵 Генерирую аудио...",
                "🔊 Подготавливаю голосовой ответ...",
                "🎧 Создаю звуковое сопровождение..."
            ],
            "analyzing_crypto": [
                "📈 Анализирую криптовалютные данные...",
                "💰 Изучаю рыночные тренды...",
                "📊 Обрабатываю финансовую информацию...",
                "🔮 Прогнозирую движение цен...",
                "💎 Анализирую инвестиционные возможности..."
            ],
            "processing_emotion": [
                "😊 Выбираю подходящую эмоциональную реакцию...",
                "🎭 Подготавливаю эмоциональное видео...",
                "💫 Создаю атмосферу для ответа...",
                "🌟 Настраиваю эмоциональный тон...",
                "🎪 Готовлю эмоциональное представление..."
            ],
            "finalizing": [
                "✨ Завершаю формирование ответа...",
                "🎯 Финальная обработка...",
                "🚀 Готовлю к отправке...",
                "💫 Применяю последние штрихи...",
                "🎉 Почти готово!"
            ]
        }
        
        self.active_notifications: Dict[str, str] = {}
    
    async def send_thinking_notification(self, chat_id: str, process_type: str = "thinking") -> Optional[str]:
        """Отправляет уведомление о процессе мышления"""
        try:
            from .telegram_core import send_telegram_message
            
            if process_type not in self.notification_templates:
                process_type = "thinking"
            
            import random
            message = random.choice(self.notification_templates[process_type])
            
            # Добавляем индикатор процесса
            message += " ⏳"
            
            # Отправляем уведомление
            message_id = await send_telegram_message(chat_id, message)
            
            if message_id:
                self.active_notifications[chat_id] = message_id
                logger.info(f"🧠 Отправлено уведомление о процессе '{process_type}' в чат {chat_id}")
                return message_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о мышлении: {e}")
        
        return None
    
    async def update_notification(self, chat_id: str, new_message: str) -> bool:
        """Обновляет существующее уведомление"""
        try:
            from .telegram_core import edit_telegram_message
            
            if chat_id not in self.active_notifications:
                return False
            
            message_id = self.active_notifications[chat_id]
            new_message += " ⏳"
            
            success = await edit_telegram_message(chat_id, message_id, new_message)
            
            if success:
                logger.info(f"🔄 Обновлено уведомление в чате {chat_id}: {new_message}")
                return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления уведомления: {e}")
        
        return False
    
    async def complete_notification(self, chat_id: str, final_message: str = "✅ Готово!") -> bool:
        """Завершает уведомление финальным сообщением"""
        try:
            from .telegram_core import edit_telegram_message, delete_telegram_message
            
            if chat_id not in self.active_notifications:
                return False
            
            message_id = self.active_notifications[chat_id]
            
            # Обновляем на финальное сообщение
            success = await edit_telegram_message(chat_id, message_id, final_message)
            
            if success:
                # Удаляем через 2 секунды
                await asyncio.sleep(2)
                await delete_telegram_message(chat_id, message_id)
                
                # Убираем из активных
                del self.active_notifications[chat_id]
                
                logger.info(f"✅ Завершено уведомление в чате {chat_id}")
                return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка завершения уведомления: {e}")
        
        return False
    
    async def cancel_notification(self, chat_id: str) -> bool:
        """Отменяет уведомление"""
        try:
            from .telegram_core import delete_telegram_message
            
            if chat_id not in self.active_notifications:
                return False
            
            message_id = self.active_notifications[chat_id]
            success = await delete_telegram_message(chat_id, message_id)
            
            if success:
                del self.active_notifications[chat_id]
                logger.info(f"❌ Отменено уведомление в чате {chat_id}")
                return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отмены уведомления: {e}")
        
        return False
    
    def get_active_notification(self, chat_id: str) -> Optional[str]:
        """Возвращает ID активного уведомления для чата"""
        return self.active_notifications.get(chat_id)
    
    def has_active_notification(self, chat_id: str) -> bool:
        """Проверяет есть ли активное уведомление для чата"""
        return chat_id in self.active_notifications

# Глобальный экземпляр
smart_notifications = SmartNotifications()
