"""
📁 Memory Export Trigger - Триггер "ПАМЯТЬ" для экспорта всех чанков группы
Создает текстовый файл со всеми чанками памяти группы и отправляет в Telegram
"""

import re
import logging
import time
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("chatumba.memory_export_trigger")

class MemoryExportTrigger:
    """Триггер для экспорта всех чанков памяти группы в текстовый файл"""
    
    def __init__(self):
        self.cooldown_sec = 300  # 5 минут cooldown между экспортами
        self.last_export_time = {}  # {chat_id: timestamp}
        
        # Компоненты системы памяти (инициализируются при первом использовании)
        self._memory_manager = None
        self._smart_retriever = None
        
    def is_triggered(self, message_text: str) -> bool:
        """Проверяет, содержит ли сообщение точное слово "ПАМЯТЬ" """
        pattern = r'\bПАМЯТЬ\b'
        match = re.search(pattern, message_text, re.IGNORECASE)
        
        if match:
            logger.info(f"🎯 Триггер 'ПАМЯТЬ' сработал: '{message_text[:50]}...'")
            return True
            
        return False
    
    def is_cooldown_active(self, chat_id: str) -> bool:
        """Проверяет, активен ли cooldown для чата"""
        now = time.time()
        last_time = self.last_export_time.get(chat_id, 0)
        
        if now - last_time < self.cooldown_sec:
            remaining = self.cooldown_sec - (now - last_time)
            logger.info(f"⏰ Cooldown активен для чата {chat_id}, осталось {remaining:.1f} сек")
            return True
            
        return False
    
    def update_export_time(self, chat_id: str):
        """Обновляет время последнего экспорта"""
        self.last_export_time[chat_id] = time.time()
        logger.info(f"🕐 Обновлено время экспорта для чата {chat_id}")
    
    async def process_trigger(self, chat_id: str, message_text: str, user_id: str) -> Optional[str]:
        """Обрабатывает срабатывание триггера экспорта памяти"""
        
        # Проверяем точное слово "ПАМЯТЬ"
        if not self.is_triggered(message_text):
            return None
            
        # Проверяем cooldown
        if self.is_cooldown_active(chat_id):
            return "⏰ Cooldown активен (5 минут между экспортами памяти)"
            
        # Обновляем время экспорта
        self.update_export_time(chat_id)
        
        try:
            # Инициализируем компоненты если нужно
            await self._ensure_components_initialized()
            
            # Экспортируем все чанки группы
            file_path = await self._export_group_memory(chat_id)
            
            if file_path and os.path.exists(file_path):
                # Отправляем файл в группу
                success = await self._send_memory_file(chat_id, file_path)
                
                if success:
                    # Удаляем временный файл
                    try:
                        os.remove(file_path)
                        logger.info(f"🗑️ Временный файл удален: {file_path}")
                    except:
                        pass
                    
                    return "📁 Экспорт памяти завершен! Файл отправлен в группу."
                else:
                    return "❌ Ошибка отправки файла памяти"
            else:
                return "❌ Ошибка создания файла памяти"
                
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта памяти: {e}")
            return "❌ Ошибка экспорта памяти группы"
    
    async def _ensure_components_initialized(self):
        """Инициализирует компоненты системы памяти"""
        try:
            if self._memory_manager is None:
                from memory.smart_memory_manager import get_smart_memory_manager
                self._memory_manager = get_smart_memory_manager()
                logger.debug("📊 SmartMemoryManager инициализирован")
            
            if self._smart_retriever is None:
                from memory.smart_retriever import get_smart_retriever
                self._smart_retriever = get_smart_retriever(self._memory_manager)
                logger.debug("🔍 SmartRetriever инициализирован")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации компонентов: {e}")
            raise
    
    async def _export_group_memory(self, chat_id: str) -> Optional[str]:
        """Экспортирует все чанки памяти группы в текстовый файл"""
        try:
            logger.info(f"📁 Начинаем экспорт памяти для группы {chat_id}")
            
            # Получаем все чанки группы
            all_chunks = await self._get_all_group_chunks(chat_id)
            
            if not all_chunks:
                logger.warning(f"📭 Нет чанков памяти для группы {chat_id}")
                return None
            
            logger.info(f"📊 Найдено {len(all_chunks)} чанков для экспорта")
            
            # Создаем временный файл
            temp_dir = Path(__file__).parent.parent.parent / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"memory_export_{chat_id}_{timestamp}.txt"
            file_path = temp_dir / filename
            
            # Формируем содержимое файла
            content = self._format_memory_chunks(all_chunks, chat_id)
            
            # Записываем в файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ Файл памяти создан: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта памяти: {e}")
            return None
    
    async def _get_all_group_chunks(self, chat_id: str) -> List[Any]:
        """Получает все чанки памяти группы"""
        try:
            # Используем новый метод SmartRetriever для получения всех чанков
            chunks = await self._smart_retriever.get_all_group_chunks(chat_id)
            
            logger.info(f"📊 Получено {len(chunks)} чанков для группы {chat_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения чанков: {e}")
            return []
    
    def _format_memory_chunks(self, chunks: List[Any], chat_id: str) -> str:
        """Форматирует чанки памяти в читаемый текст"""
        try:
            content = []
            
            # Заголовок
            content.append("=" * 80)
            content.append(f"🧠 ЭКСПОРТ ПАМЯТИ ГРУППЫ {chat_id}")
            content.append(f"📅 Дата экспорта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            content.append(f"📊 Количество чанков: {len(chunks)}")
            content.append("=" * 80)
            content.append("")
            
            # Сортируем чанки по времени создания (новые первыми)
            sorted_chunks = sorted(chunks, key=lambda x: x.created_at, reverse=True)
            
            # Форматируем каждый чанк
            for i, chunk in enumerate(sorted_chunks, 1):
                content.append(f"📝 ЧАНК #{i}")
                content.append(f"🆔 ID: {chunk.id}")
                content.append(f"📅 Создан: {datetime.fromtimestamp(chunk.created_at).strftime('%Y-%m-%d %H:%M:%S')}")
                content.append(f"⏰ Период: {datetime.fromtimestamp(chunk.source_period_start).strftime('%d.%m %H:%M')} - {datetime.fromtimestamp(chunk.source_period_end).strftime('%d.%m %H:%M')}")
                content.append(f"👥 Участники: {', '.join(chunk.participants)}")
                content.append(f"📊 Сообщений: {chunk.message_count}")
                content.append(f"⭐ Релевантность: {chunk.relevance_base:.2f}")
                content.append(f"🏷️ Тема: {chunk.topic}")
                content.append("")
                content.append("📄 СОДЕРЖАНИЕ:")
                content.append("-" * 40)
                content.append(chunk.content)
                content.append("-" * 40)
                content.append("")
                content.append("=" * 80)
                content.append("")
            
            # Статистика
            content.append("📈 СТАТИСТИКА:")
            content.append(f"• Всего чанков: {len(chunks)}")
            
            # Группировка по темам
            topics = {}
            for chunk in chunks:
                topic = chunk.topic
                if topic not in topics:
                    topics[topic] = 0
                topics[topic] += 1
            
            content.append("• По темам:")
            for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True):
                content.append(f"  - {topic}: {count} чанков")
            
            # Группировка по участникам
            participants = {}
            for chunk in chunks:
                for participant in chunk.participants:
                    if participant not in participants:
                        participants[participant] = 0
                    participants[participant] += 1
            
            content.append("• По участникам:")
            for participant, count in sorted(participants.items(), key=lambda x: x[1], reverse=True):
                content.append(f"  - {participant}: {count} упоминаний")
            
            content.append("")
            content.append("=" * 80)
            content.append("🤖 Экспорт создан системой IKAR (Чатумба)")
            content.append("=" * 80)
            
            return "\n".join(content)
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования чанков: {e}")
            return f"Ошибка форматирования: {e}"
    
    async def _send_memory_file(self, chat_id: str, file_path: str) -> bool:
        """Отправляет файл памяти в Telegram группу"""
        try:
            from api.telegram_core import send_telegram_document
            
            # Отправляем файл как документ
            success = await send_telegram_document(chat_id, file_path, "memory_export.txt")
            
            if success:
                logger.info(f"✅ Файл памяти отправлен в группу {chat_id}")
                return True
            else:
                logger.error(f"❌ Ошибка отправки файла в группу {chat_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки файла: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику триггера"""
        return {
            "active_chats": len(self.last_export_time),
            "cooldown_seconds": self.cooldown_sec,
            "last_exports": self.last_export_time.copy(),
            "components_initialized": {
                "memory_manager": self._memory_manager is not None,
                "smart_retriever": self._smart_retriever is not None
            }
        }

# Создаем глобальный экземпляр триггера
memory_export_trigger = MemoryExportTrigger()

# Функция для удобного использования
async def process_memory_export_trigger(chat_id: str, message_text: str, user_id: str) -> Optional[str]:
    """Удобная функция для обработки триггера экспорта памяти"""
    return await memory_export_trigger.process_trigger(chat_id, message_text, user_id)
