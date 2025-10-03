"""
🔍 Smart Retriever - Умный поисковик памяти с временным затуханием
Ищет релевантные чанки с учетом возраста и контекста
"""

import logging
import sqlite3
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re

from .smart_memory_manager import SmartMemoryManager, MemoryChunk

logger = logging.getLogger("chatumba.smart_retriever")

@dataclass
class RelevantChunk:
    """Релевантный чанк с метриками"""
    chunk: MemoryChunk
    relevance_score: float
    age_days: float
    threshold_passed: bool
    time_bonus: float
    context_bonus: float

class SmartRetriever:
    """Умный поисковик памяти"""
    
    def __init__(self, memory_manager: SmartMemoryManager):
        self.memory_manager = memory_manager
        
        # Настройки поиска
        self.max_chunks = 5  # Максимум чанков в результате
        self.base_relevance_weight = 0.6
        self.time_relevance_weight = 0.2
        self.context_relevance_weight = 0.2
        
        # Временные бонусы
        self.time_of_day_bonus = {
            'morning': ['утро', 'работа', 'планы', 'встреча'],
            'afternoon': ['обед', 'работа', 'проект', 'задача'],
            'evening': ['вечер', 'отдых', 'планы', 'встреча'],
            'night': ['ночь', 'завтра', 'поздно', 'спать']
        }
        
        # Контекстные ключевые слова
        self.context_keywords = {
            'work': ['работа', 'проект', 'задача', 'встреча', 'дедлайн', 'код'],
            'personal': ['дом', 'семья', 'друзья', 'отдых', 'хобби'],
            'plans': ['планы', 'завтра', 'встреча', 'событие', 'напоминание'],
            'problems': ['проблема', 'ошибка', 'не работает', 'помощь', 'вопрос']
        }
        
        # Ключевые слова для запросов о памяти
        self.memory_query_keywords = [
            'что помнишь', 'что запомнил', 'что знаешь', 'расскажи что помнишь',
            'покажи память', 'что в памяти', 'вся память', 'все что помнишь',
            'что сохранил', 'что записал', 'все знания', 'вся информация',
            'память', 'ПАМЯТЬ'  # Добавляем триггер экспорта памяти
        ]
    
    async def find_relevant_chunks(self, chat_id: str, query: str, context: str = "") -> List[RelevantChunk]:
        """Находит релевантные чанки памяти"""
        try:
            logger.info(f"🔍 Поиск релевантных чанков для чата {chat_id}")
            logger.debug(f"Query: {query[:100]}...")
            
            # Проверяем, является ли это запросом о памяти
            is_memory_query = self._is_memory_query(query)
            
            # Получаем все чанки чата
            all_chunks = await self._get_chat_chunks(chat_id)
            
            if not all_chunks:
                logger.info("📭 Нет чанков для поиска")
                return []
            
            # Если это запрос о памяти - возвращаем все чанки
            if is_memory_query:
                logger.info(f"🧠 Запрос о памяти - возвращаем все {len(all_chunks)} чанков")
                relevant_chunks = []
                current_time = time.time()
                
                for chunk in all_chunks:
                    age_days = (current_time - chunk.created_at) / (24 * 3600)
                    relevant_chunk = RelevantChunk(
                        chunk=chunk,
                        relevance_score=1.0,  # Максимальная релевантность для запросов о памяти
                        age_days=age_days,
                        threshold_passed=True,
                        time_bonus=0.0,
                        context_bonus=0.0
                    )
                    relevant_chunks.append(relevant_chunk)
                
                # Сортируем по времени создания (новые первыми)
                relevant_chunks.sort(key=lambda x: x.chunk.created_at, reverse=True)
                return relevant_chunks
            
            # Обычный поиск с фильтрацией
            relevant_chunks = []
            current_time = time.time()
            time_info = self.memory_manager.get_current_time_info()
            
            for chunk in all_chunks:
                # Вычисляем возраст чанка
                age_days = (current_time - chunk.created_at) / (24 * 3600)
                
                # Получаем порог релевантности для этого возраста
                threshold = self.memory_manager.calculate_relevance_threshold(age_days)
                
                # Вычисляем релевантность
                relevance_score = await self._calculate_relevance(chunk, query, context, time_info)
                
                # Проверяем, прошел ли чанк порог
                if relevance_score >= threshold:
                    # Вычисляем бонусы
                    time_bonus = self._calculate_time_bonus(chunk, time_info)
                    context_bonus = self._calculate_context_bonus(chunk, context)
                    
                    relevant_chunk = RelevantChunk(
                        chunk=chunk,
                        relevance_score=relevance_score,
                        age_days=age_days,
                        threshold_passed=True,
                        time_bonus=time_bonus,
                        context_bonus=context_bonus
                    )
                    relevant_chunks.append(relevant_chunk)
                else:
                    logger.debug(f"❌ Чанк {chunk.id} не прошел порог: {relevance_score:.3f} < {threshold:.3f}")
            
            # Сортируем по итоговой релевантности
            relevant_chunks.sort(key=lambda x: x.relevance_score + x.time_bonus + x.context_bonus, reverse=True)
            
            # Ограничиваем количество
            result = relevant_chunks[:self.max_chunks]
            
            logger.info(f"✅ Найдено {len(result)} релевантных чанков из {len(all_chunks)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска релевантных чанков: {e}")
            return []
    
    async def _get_chat_chunks(self, chat_id: str) -> List[MemoryChunk]:
        """Получает все чанки чата"""
        try:
            conn = sqlite3.connect(self.memory_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, chat_id, topic, content, created_at, source_period_start,
                       source_period_end, relevance_base, message_count, participants
                FROM memory_chunks
                WHERE chat_id = ?
                ORDER BY created_at DESC
            """, (chat_id,))
            
            chunks = []
            for row in cursor.fetchall():
                participants = json.loads(row[9]) if row[9] else []
                
                chunk = MemoryChunk(
                    id=row[0],
                    chat_id=row[1],
                    topic=row[2],
                    content=row[3],
                    created_at=row[4],
                    source_period_start=row[5],
                    source_period_end=row[6],
                    relevance_base=row[7],
                    message_count=row[8],
                    participants=participants
                )
                chunks.append(chunk)
            
            conn.close()
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения чанков чата: {e}")
            return []
    
    async def _calculate_relevance(self, chunk: MemoryChunk, query: str, context: str, time_info: Dict[str, Any]) -> float:
        """Вычисляет базовую релевантность чанка"""
        try:
            # Извлекаем ключевые слова из запроса
            query_keywords = self._extract_keywords(query.lower())
            context_keywords = self._extract_keywords(context.lower())
            
            # Текст чанка для поиска
            chunk_text = f"{chunk.topic} {chunk.content}".lower()
            
            # Базовая релевантность по ключевым словам
            keyword_score = 0.0
            total_keywords = len(query_keywords) + len(context_keywords)
            
            if total_keywords > 0:
                matches = 0
                for keyword in query_keywords + context_keywords:
                    if keyword in chunk_text:
                        matches += 1
                
                keyword_score = matches / total_keywords
            
            # Семантическая близость (упрощенная)
            semantic_score = self._calculate_semantic_similarity(query, chunk_text)
            
            # Базовая важность чанка
            importance_score = chunk.relevance_base
            
            # Итоговая релевантность
            relevance = (
                keyword_score * self.base_relevance_weight +
                semantic_score * 0.3 +
                importance_score * 0.1
            )
            
            logger.debug(f"📊 Чанк {chunk.id}: keyword={keyword_score:.3f}, semantic={semantic_score:.3f}, importance={importance_score:.3f} → {relevance:.3f}")
            
            return relevance
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления релевантности: {e}")
            return 0.0
    
    def _is_memory_query(self, query: str) -> bool:
        """Проверяет, является ли запрос запросом о памяти"""
        query_lower = query.lower().strip()
        
        # Проверяем точные совпадения
        for keyword in self.memory_query_keywords:
            if keyword in query_lower:
                return True
        
        # Проверяем паттерны
        memory_patterns = [
            r'бот.*что.*помнишь',
            r'бот.*что.*запомнил',
            r'бот.*что.*знаешь',
            r'бот.*расскажи.*память',
            r'бот.*покажи.*память',
            r'бот.*вся.*память',
            r'бот.*все.*помнишь'
        ]
        
        for pattern in memory_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    async def get_all_group_chunks(self, chat_id: str) -> List[Any]:
        """Получает все чанки памяти для группы"""
        try:
            logger.info(f"📊 Получение всех чанков для группы {chat_id}")
            
            # Получаем все чанки группы из базы данных
            all_chunks = await self._get_chat_chunks(chat_id)
            
            if not all_chunks:
                logger.info(f"📭 Нет чанков для группы {chat_id}")
                return []
            
            logger.info(f"📊 Найдено {len(all_chunks)} чанков для группы {chat_id}")
            return all_chunks
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения всех чанков группы: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлекает ключевые слова из текста"""
        # Удаляем стоп-слова
        stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об',
            'что', 'это', 'как', 'где', 'когда', 'почему', 'если', 'то', 'же',
            'а', 'но', 'или', 'да', 'нет', 'не', 'ни', 'бы', 'ли', 'уже', 'еще'
        }
        
        # Извлекаем слова длиной от 3 символов
        words = re.findall(r'\b\w{3,}\b', text)
        keywords = [word for word in words if word not in stop_words]
        
        return list(set(keywords))  # Уникальные ключевые слова
    
    def _calculate_semantic_similarity(self, query: str, chunk_text: str) -> float:
        """Вычисляет семантическую близость (упрощенная версия)"""
        try:
            # Простая метрика на основе общих слов
            query_words = set(self._extract_keywords(query.lower()))
            chunk_words = set(self._extract_keywords(chunk_text.lower()))
            
            if not query_words or not chunk_words:
                return 0.0
            
            # Коэффициент Жаккара
            intersection = len(query_words & chunk_words)
            union = len(query_words | chunk_words)
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления семантической близости: {e}")
            return 0.0
    
    def _calculate_time_bonus(self, chunk: MemoryChunk, time_info: Dict[str, Any]) -> float:
        """Вычисляет временной бонус"""
        try:
            time_of_day = time_info.get('time_of_day', 'day')
            bonus_keywords = self.time_of_day_bonus.get(time_of_day, [])
            
            chunk_text = f"{chunk.topic} {chunk.content}".lower()
            
            bonus = 0.0
            for keyword in bonus_keywords:
                if keyword in chunk_text:
                    bonus += 0.1
            
            # Дополнительный бонус для недавних чанков в рабочее время
            if time_info.get('hour', 12) in range(9, 18):  # Рабочие часы
                age_hours = (time.time() - chunk.created_at) / 3600
                if age_hours < 24:  # Чанки младше суток
                    bonus += 0.05
            
            return min(bonus, 0.3)  # Максимальный бонус 0.3
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления временного бонуса: {e}")
            return 0.0
    
    def _calculate_context_bonus(self, chunk: MemoryChunk, context: str) -> float:
        """Вычисляет контекстный бонус"""
        try:
            if not context:
                return 0.0
            
            context_lower = context.lower()
            chunk_text = f"{chunk.topic} {chunk.content}".lower()
            
            bonus = 0.0
            
            # Проверяем контекстные категории
            for category, keywords in self.context_keywords.items():
                context_matches = sum(1 for kw in keywords if kw in context_lower)
                chunk_matches = sum(1 for kw in keywords if kw in chunk_text)
                
                if context_matches > 0 and chunk_matches > 0:
                    bonus += 0.1 * min(context_matches, chunk_matches)
            
            return min(bonus, 0.2)  # Максимальный бонус 0.2
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления контекстного бонуса: {e}")
            return 0.0
    
    def format_chunks_for_prompt(self, relevant_chunks: List[RelevantChunk], time_info: Dict[str, Any]) -> str:
        """Форматирует чанки для включения в промпт"""
        if not relevant_chunks:
            return ""
        
        current_time_str = time_info.get('datetime', 'неизвестно')
        
        formatted_parts = [
            f"=== ПАМЯТЬ ГРУППЫ ===",
            f"Текущее время: {current_time_str}",
            ""
        ]
        
        for i, rel_chunk in enumerate(relevant_chunks, 1):
            chunk = rel_chunk.chunk
            
            # Форматируем время создания чанка
            chunk_time = datetime.fromtimestamp(chunk.created_at)
            age_str = self._format_age(rel_chunk.age_days)
            
            # Период исходных сообщений
            period_start = datetime.fromtimestamp(chunk.source_period_start)
            period_end = datetime.fromtimestamp(chunk.source_period_end)
            
            formatted_parts.extend([
                f"{i}. 📝 {chunk.topic} ({age_str})",
                f"   Период: {period_start.strftime('%d.%m %H:%M')} - {period_end.strftime('%d.%m %H:%M')}",
                f"   Участники: {', '.join(chunk.participants[:3])}{'...' if len(chunk.participants) > 3 else ''}",
                f"   Содержание: {chunk.content}",
                f"   Релевантность: {rel_chunk.relevance_score:.2f} (порог пройден)",
                ""
            ])
        
        formatted_parts.extend([
            "=== ИНСТРУКЦИЯ ===",
            "Используй эту память для контекста, но приоритет у ТЕКУЩЕГО разговора.",
            "Если память противоречит текущей ситуации - игнорируй память.",
            "Учитывай время: старая информация может быть неактуальной.",
            ""
        ])
        
        return "\n".join(formatted_parts)
    
    def _format_age(self, age_days: float) -> str:
        """Форматирует возраст чанка"""
        if age_days < 1:
            hours = int(age_days * 24)
            return f"{hours}ч назад"
        elif age_days < 7:
            return f"{int(age_days)}д назад"
        elif age_days < 30:
            weeks = int(age_days / 7)
            return f"{weeks}нед назад"
        else:
            months = int(age_days / 30)
            return f"{months}мес назад"
    
    async def get_retriever_stats(self, chat_id: str) -> Dict[str, Any]:
        """Получает статистику поисковика для чата"""
        try:
            chunks = await self._get_chat_chunks(chat_id)
            
            if not chunks:
                return {'total_chunks': 0}
            
            current_time = time.time()
            age_distribution = {'fresh': 0, 'recent': 0, 'old': 0, 'ancient': 0}
            
            for chunk in chunks:
                age_days = (current_time - chunk.created_at) / (24 * 3600)
                if age_days <= 7:
                    age_distribution['fresh'] += 1
                elif age_days <= 30:
                    age_distribution['recent'] += 1
                elif age_days <= 90:
                    age_distribution['old'] += 1
                else:
                    age_distribution['ancient'] += 1
            
            return {
                'total_chunks': len(chunks),
                'age_distribution': age_distribution,
                'oldest_chunk_days': max((current_time - chunk.created_at) / (24 * 3600) for chunk in chunks),
                'newest_chunk_days': min((current_time - chunk.created_at) / (24 * 3600) for chunk in chunks),
                'avg_relevance_base': sum(chunk.relevance_base for chunk in chunks) / len(chunks)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики поисковика: {e}")
            return {}

# Глобальный экземпляр поисковика
_smart_retriever = None

def get_smart_retriever(memory_manager: SmartMemoryManager = None) -> SmartRetriever:
    """Получает глобальный экземпляр умного поисковика"""
    global _smart_retriever
    if _smart_retriever is None and memory_manager:
        _smart_retriever = SmartRetriever(memory_manager)
    return _smart_retriever