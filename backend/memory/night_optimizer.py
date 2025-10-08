"""
🌙 Night Optimizer - Ночная система сжатия сообщений в смысловые чанки
Работает с 23:00 до 07:00, группирует сообщения по темам и сжимает через LLM
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import asdict
import hashlib

from .smart_memory_manager import SmartMemoryManager, MemoryMessage, MemoryChunk

logger = logging.getLogger("chatumba.night_optimizer")

class NightOptimizer:
    """Ночной оптимизатор памяти"""
    
    def __init__(self, memory_manager: SmartMemoryManager, llm_client):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.is_running = False
        self.optimization_interval = 1800  # 30 минут между циклами
        
        # Настройки группировки сообщений
        self.min_messages_for_chunk = 5  # Минимум сообщений для создания чанка
        self.max_time_gap_hours = 6      # Максимальный разрыв между сообщениями в одной группе
        self.chunk_period_hours = 24     # Период для группировки (24 часа)
        
    async def start_night_optimization(self):
        """Запускает ночную оптимизацию"""
        self.is_running = True
        logger.info("🌙 Запуск ночной оптимизации памяти")
        
        while self.is_running:
            try:
                is_night = self.memory_manager._is_night_time()
                logger.info(f"🌙 Проверка ночного времени: {is_night}")
                
                if is_night:
                    logger.info("🌙 Ночное время - ОТКЛЮЧЕНО (жрет ключи)")
                    # await self._run_optimization_cycle()  # ОТКЛЮЧЕНО
                else:
                    logger.info("☀️ Дневное время - пропускаем оптимизацию")
                
                await asyncio.sleep(self.optimization_interval)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле ночной оптимизации: {e}")
                await asyncio.sleep(300)  # 5 минут при ошибке
    
    def stop_night_optimization(self):
        """Останавливает ночную оптимизацию"""
        self.is_running = False
        logger.info("🛑 Остановка ночной оптимизации памяти")
    
    async def _run_optimization_cycle(self):
        """Выполняет один цикл оптимизации"""
        logger.info("🔄 Начинаем цикл ночной оптимизации")
        
        try:
            # Получаем необработанные сообщения
            unprocessed_messages = await self._get_unprocessed_messages()
            
            if not unprocessed_messages:
                logger.debug("📭 Нет необработанных сообщений")
                return
            
            # Группируем по чатам
            messages_by_chat = self._group_messages_by_chat(unprocessed_messages)
            
            # Обрабатываем каждый чат
            for chat_id, messages in messages_by_chat.items():
                await self._optimize_chat_messages(chat_id, messages)
            
            logger.info(f"✅ Цикл оптимизации завершен. Обработано чатов: {len(messages_by_chat)}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в цикле оптимизации: {e}")
    
    async def _get_unprocessed_messages(self) -> List[MemoryMessage]:
        """Получает необработанные сообщения только из основной группы"""
        try:
            import sqlite3
            import os
            
            conn = sqlite3.connect(self.memory_manager.db_path)
            cursor = conn.cursor()
            
            # Получаем ID основной группы из .env
            main_chat_id = os.getenv('TELEGRAM_CHANNEL_ID', '-1002952589195')
            
            # Берем сообщения старше 1 часа (чтобы не мешать активному общению)
            cutoff_time = time.time() - 3600
            
            cursor.execute("""
                SELECT id, chat_id, user_id, content, timestamp, processed
                FROM group_messages
                WHERE processed = FALSE AND timestamp < ? AND chat_id = ?
                ORDER BY timestamp
            """, (cutoff_time, main_chat_id))
            
            messages = []
            for row in cursor.fetchall():
                messages.append(MemoryMessage(
                    id=row[0],
                    chat_id=row[1],
                    user_id=row[2],
                    content=row[3],
                    timestamp=row[4],
                    processed=bool(row[5])
                ))
            
            conn.close()
            logger.info(f"📊 Найдено {len(messages)} необработанных сообщений из основной группы {main_chat_id}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения необработанных сообщений: {e}")
            return []
    
    def _group_messages_by_chat(self, messages: List[MemoryMessage]) -> Dict[str, List[MemoryMessage]]:
        """Группирует сообщения по чатам"""
        grouped = {}
        for message in messages:
            if message.chat_id not in grouped:
                grouped[message.chat_id] = []
            grouped[message.chat_id].append(message)
        return grouped
    
    async def _optimize_chat_messages(self, chat_id: str, messages: List[MemoryMessage]):
        """Оптимизирует сообщения одного чата"""
        try:
            logger.info(f"🔧 Оптимизируем чат {chat_id}: {len(messages)} сообщений")
            
            # Группируем сообщения по временным периодам
            message_groups = self._group_messages_by_time(messages)
            
            # Создаем чанки для каждой группы (с rate limiting)
            processed_groups = 0
            max_groups_per_cycle = 5  # Максимум 5 групп за цикл
            
            for group in message_groups:
                if processed_groups >= max_groups_per_cycle:
                    logger.info(f"⏸️ Достигнут лимит групп за цикл ({max_groups_per_cycle}), останавливаемся")
                    break
                    
                if len(group) >= self.min_messages_for_chunk:
                    chunk = await self._create_memory_chunk(chat_id, group)
                    if chunk:
                        await self._save_memory_chunk(chunk)
                        await self._mark_messages_processed([msg.id for msg in group])
                        processed_groups += 1
                        
                        # Rate limiting: пауза между запросами
                        await asyncio.sleep(2)
                else:
                    # Если сообщений мало, просто помечаем как обработанные
                    await self._mark_messages_processed([msg.id for msg in group])
                    logger.debug(f"⚠️ Группа из {len(group)} сообщений слишком мала для чанка")
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации чата {chat_id}: {e}")
    
    def _group_messages_by_time(self, messages: List[MemoryMessage]) -> List[List[MemoryMessage]]:
        """Группирует сообщения по временным периодам"""
        if not messages:
            return []
        
        # Сортируем по времени
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        
        groups = []
        current_group = [sorted_messages[0]]
        
        for message in sorted_messages[1:]:
            # Если разрыв больше max_time_gap_hours, начинаем новую группу
            time_gap = message.timestamp - current_group[-1].timestamp
            if time_gap > (self.max_time_gap_hours * 3600):
                groups.append(current_group)
                current_group = [message]
            else:
                current_group.append(message)
        
        # Добавляем последнюю группу
        if current_group:
            groups.append(current_group)
        
        logger.debug(f"📦 Создано {len(groups)} временных групп сообщений")
        return groups
    
    async def _create_memory_chunk(self, chat_id: str, messages: List[MemoryMessage]) -> Optional[MemoryChunk]:
        """Создает чанк памяти из группы сообщений"""
        try:
            # Подготавливаем данные для LLM
            conversation_text = self._format_messages_for_llm(messages)
            participants = list(set(msg.user_id for msg in messages))
            
            # Генерируем сжатый чанк через LLM
            chunk_data = await self._compress_messages_with_llm(conversation_text, participants)
            
            if not chunk_data:
                logger.warning("⚠️ LLM не смог создать чанк")
                return None
            
            # Создаем чанк
            chunk_id = hashlib.md5(f"{chat_id}_{messages[0].timestamp}_{len(messages)}".encode()).hexdigest()[:16]
            
            chunk = MemoryChunk(
                id=chunk_id,
                chat_id=chat_id,
                topic=chunk_data.get('topic', 'Общение'),
                content=chunk_data.get('summary', ''),
                created_at=time.time(),
                source_period_start=messages[0].timestamp,
                source_period_end=messages[-1].timestamp,
                relevance_base=chunk_data.get('importance', 0.5),
                message_count=len(messages),
                participants=participants
            )
            
            logger.info(f"✅ Создан чанк {chunk_id}: {chunk.topic}")
            return chunk
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания чанка: {e}")
            return None
    
    def _format_messages_for_llm(self, messages: List[MemoryMessage]) -> str:
        """Форматирует сообщения для отправки в LLM"""
        formatted_lines = []
        
        for msg in messages:
            timestamp_str = datetime.fromtimestamp(msg.timestamp).strftime('%H:%M')
            user_short = msg.user_id[-4:] if len(msg.user_id) > 4 else msg.user_id
            formatted_lines.append(f"[{timestamp_str}] {user_short}: {msg.content}")
        
        return "\n".join(formatted_lines)
    
    async def _compress_messages_with_llm(self, conversation_text: str, participants: List[str]) -> Optional[Dict[str, Any]]:
        """Сжимает сообщения через LLM"""
        try:
            # Системный промпт для сжатия
            system_prompt = """Ты - система сжатия групповых разговоров. 
Твоя задача - создать краткое, но информативное резюме разговора.

ВЕРНИ ТОЛЬКО JSON:
{
    "topic": "Краткая тема разговора",
    "summary": "Подробное резюме: кто что обсуждал, какие решения приняли, важные детали",
    "importance": 0.1-1.0,
    "key_points": ["ключевой момент 1", "ключевой момент 2"],
    "participants_activity": {"user1": "что делал", "user2": "что делал"}
}

ПРАВИЛА:
- Сохраняй ВСЮ важную информацию
- Убирай флуд и бессмысленные сообщения  
- Указывай конкретные решения и планы
- Отмечай эмоциональные моменты
- Importance: 0.1-0.3 (флуд), 0.4-0.6 (обычное общение), 0.7-1.0 (важные решения)"""
            
            user_message = f"""РАЗГОВОР В ГРУППЕ:
Участники: {', '.join(participants)}

{conversation_text}

Создай JSON резюме этого разговора."""
            
            # ЛОГИРУЕМ ПРОМПТ (DEBUG уровень)
            logger.debug(f"🔍 SYSTEM PROMPT: {system_prompt}")
            logger.debug(f"🔍 USER MESSAGE: {user_message}")
            
            response = await self.llm_client.chat_completion(
                user_message=user_message,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=2000
            )
            
            # ЛОГИРУЕМ ОТВЕТ (DEBUG уровень)
            logger.debug(f"🔍 RAW RESPONSE: {response}")
            
            # Проверяем что ответ не пустой
            if not response or not response.strip():
                logger.error("❌ Получен пустой ответ от LLM")
                return None
            
            # Парсим JSON ответ
            chunk_data = self._parse_llm_json_response(response)
            return chunk_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка сжатия через LLM: {e}")
            return None
    
    def _parse_llm_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Парсит JSON ответ от LLM с использованием крутого парсера"""
        try:
            # Проверяем, что ответ не пустой
            if not response or not response.strip():
                logger.warning("⚠️ Получен пустой ответ от LLM")
                return None
            
            logger.info(f"🔍 Парсим ответ LLM: {response[:200]}...")
            
            # Импортируем крутой парсер
            from utils.robust_json_parser import robust_json_parser
            
            # Очищаем от тегов <think> для DeepSeek R1
            cleaned_response = response
            if "<think>" in response and "</think>" in response:
                # Убираем блок рассуждений
                parts = response.split("</think>")
                if len(parts) > 1:
                    cleaned_response = parts[-1].strip()
                    logger.debug("🧠 Убрали блок <think> из ответа DeepSeek R1")
            
            # Используем крутой парсер
            json_objects = robust_json_parser(cleaned_response)
            
            if not json_objects:
                logger.warning("⚠️ Крутой парсер не нашел JSON объектов")
                logger.info(f"🔍 ОЧИЩЕННЫЙ ОТВЕТ: {cleaned_response}")
                return None
            
            # Берем первый найденный объект
            data = json_objects[0]
            logger.info(f"✅ Успешно распарсен JSON: {list(data.keys())}")
            
            # Валидируем обязательные поля
            if not all(key in data for key in ['topic', 'summary', 'importance']):
                logger.warning("⚠️ JSON от LLM не содержит обязательных полей")
                # Пытаемся восстановить недостающие поля
                if 'topic' not in data:
                    data['topic'] = 'Общение'
                if 'summary' not in data:
                    data['summary'] = 'Краткое обсуждение'
                if 'importance' not in data:
                    data['importance'] = 0.5
            
            # Нормализуем importance
            data['importance'] = max(0.1, min(1.0, float(data.get('importance', 0.5))))
            
            logger.info(f"✅ Крутой парсер успешно извлек JSON: {data.get('topic', 'без темы')}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Ошибка крутого парсера JSON: {e}")
            logger.error(f"🔍 ПОЛНЫЙ ОТВЕТ LLM: {response}")
            return None
    
    async def _save_memory_chunk(self, chunk: MemoryChunk) -> bool:
        """Сохраняет чанк в базу данных"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.memory_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO memory_chunks 
                (id, chat_id, topic, content, created_at, source_period_start, 
                 source_period_end, relevance_base, message_count, participants, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk.id,
                chunk.chat_id,
                chunk.topic,
                chunk.content,
                chunk.created_at,
                chunk.source_period_start,
                chunk.source_period_end,
                chunk.relevance_base,
                chunk.message_count,
                json.dumps(chunk.participants),
                json.dumps(asdict(chunk))
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Чанк {chunk.id} сохранен в базу данных")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения чанка: {e}")
            return False
    
    async def _mark_messages_processed(self, message_ids: List[int]) -> bool:
        """Помечает сообщения как обработанные"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.memory_manager.db_path)
            cursor = conn.cursor()
            
            # Обновляем статус сообщений
            placeholders = ','.join('?' * len(message_ids))
            cursor.execute(f"""
                UPDATE group_messages 
                SET processed = TRUE 
                WHERE id IN ({placeholders})
            """, message_ids)
            
            updated_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.debug(f"✅ Помечено как обработанные: {updated_count} сообщений")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статуса сообщений: {e}")
            return False
    
    async def force_optimize_chat(self, chat_id: str) -> Dict[str, Any]:
        """Принудительная оптимизация конкретного чата (для тестирования)"""
        try:
            logger.info(f"🔧 Принудительная оптимизация чата {chat_id}")
            
            # Получаем необработанные сообщения чата
            import sqlite3
            conn = sqlite3.connect(self.memory_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, chat_id, user_id, content, timestamp, processed
                FROM group_messages
                WHERE chat_id = ? AND processed = FALSE
                ORDER BY timestamp
            """, (chat_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append(MemoryMessage(
                    id=row[0],
                    chat_id=row[1],
                    user_id=row[2],
                    content=row[3],
                    timestamp=row[4],
                    processed=bool(row[5])
                ))
            
            conn.close()
            
            if not messages:
                return {'status': 'no_messages', 'message': 'Нет необработанных сообщений'}
            
            # Оптимизируем
            await self._optimize_chat_messages(chat_id, messages)
            
            return {
                'status': 'success',
                'processed_messages': len(messages),
                'message': f'Обработано {len(messages)} сообщений'
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка принудительной оптимизации: {e}")
            return {'status': 'error', 'message': str(e)}

# Глобальный экземпляр оптимизатора
_night_optimizer = None

def get_night_optimizer(memory_manager: SmartMemoryManager = None, llm_client = None) -> NightOptimizer:
    """Получает глобальный экземпляр ночного оптимизатора"""
    global _night_optimizer
    if _night_optimizer is None and memory_manager and llm_client:
        _night_optimizer = NightOptimizer(memory_manager, llm_client)
    return _night_optimizer
