"""
Система интеллектуальной инъекции коллективной памяти в промпты
Оптимизирована для DeepSeek с контекстным окном 160K токенов
"""

import asyncio
import json
import re
import sys
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import tiktoken
import time

# Добавляем путь к backend в sys.path для корректных импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.collective_mind import get_collective_mind, CollectiveMemory
from utils.logger import get_logger

# Получаем логгер для этого модуля
logger = get_logger('memory_injector')


@dataclass
class MemoryChunk:
    """Чанк памяти для инъекции в промпт"""
    id: str = ""
    content: str = ""
    relevance_score: float = 0.0
    memory_type: str = ""
    source_agent: str = ""
    agent_id: str = ""
    importance: float = 0.0
    tokens_count: int = 0
    context_tags: List[str] = None
    timestamp: float = 0.0
    success_rate: float = 0.0
    
    def __post_init__(self):
        if self.context_tags is None:
            self.context_tags = []


class MemoryInjector:
    """Система инъекции коллективной памяти в промпты"""
    
    def __init__(self):
        self.collective_mind = get_collective_mind()
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")  # Совместимый токенизатор
        
        # Параметры для DeepSeek
        self.max_context_tokens = 160000  # 160K токенов
        self.memory_budget_ratio = 0.3    # 30% контекста для памяти
        self.max_memory_tokens = int(self.max_context_tokens * self.memory_budget_ratio)
        
        # Приоритеты типов памяти
        self.memory_type_weights = {
            'insight': 1.0,
            'wisdom': 0.9,
            'experience': 0.8,
            'observation': 0.7,
            'reflection': 0.6
        }
        
        # Сбалансированный порог релевантности
        self.min_relevance_threshold = 0.5  # Понижен с 0.7 до 0.5 для лучшего покрытия
        self.high_relevance_threshold = 0.8  # Для очень высокорелевантных воспоминаний
        
        # Кеш для оптимизации
        self.relevance_cache = {}
        self.token_cache = {}
        
    def count_tokens(self, text: str) -> int:
        """Подсчет токенов в тексте"""
        if text in self.token_cache:
            return self.token_cache[text]
        
        token_count = len(self.tokenizer.encode(text))
        self.token_cache[text] = token_count
        return token_count
    
    def extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        # Удаляем стоп-слова и извлекаем значимые термины
        stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об',
            'что', 'это', 'как', 'где', 'когда', 'почему', 'если', 'то', 'же',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be'
        }
        
        # Извлекаем слова длиной от 3 символов
        words = re.findall(r'\b\w{3,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]
        
        # Возвращаем уникальные ключевые слова
        return list(set(keywords))
    
    def calculate_relevance(self, memory: CollectiveMemory, query_keywords: List[str], 
                          context_keywords: List[str]) -> float:
        """Расчет релевантности воспоминания"""
        cache_key = f"{memory.id}_{hash(tuple(query_keywords))}_{hash(tuple(context_keywords))}"
        
        if cache_key in self.relevance_cache:
            return self.relevance_cache[cache_key]
        
        # Извлекаем ключевые слова из воспоминания
        memory_keywords = self.extract_keywords(memory.content)
        memory_keywords.extend(getattr(memory, 'tags', []))
        
        # Расчет совпадений с запросом
        query_matches = len(set(query_keywords) & set(memory_keywords))
        query_relevance = query_matches / max(len(query_keywords), 1)
        
        # Расчет совпадений с контекстом
        context_matches = len(set(context_keywords) & set(memory_keywords))
        context_relevance = context_matches / max(len(context_keywords), 1)
        
        # Семантическая близость (упрощенная)
        semantic_score = 0.0
        for qword in query_keywords:
            for mword in memory_keywords:
                if qword in mword or mword in qword:
                    semantic_score += 0.1
        
        # Итоговая релевантность
        relevance = (
            query_relevance * 0.5 +
            context_relevance * 0.3 +
            semantic_score * 0.2
        )
        
        # Бонусы за тип памяти и важность
        type_bonus = self.memory_type_weights.get(memory.memory_type, 0.5)
        importance_bonus = memory.importance
        success_bonus = memory.success_rate
        
        final_relevance = relevance * (1 + type_bonus + importance_bonus + success_bonus)
        
        self.relevance_cache[cache_key] = final_relevance
        return final_relevance
    
    async def select_relevant_memories(self, query: str, context: str, user_id: str = None,
                                     max_memories: int = 10) -> List[MemoryChunk]:  # Было 50, теперь 10
        """Выбор релевантных воспоминаний"""
        # Логирование отладки памяти
        try:
            import sys
            sys.path.append('backend')
            from utils.memory_debug_logger import get_memory_debug_logger
        except ImportError:
            # Fallback - создаем заглушку
            class DummyLogger:
                def log_memory_injector_start(self, *args): pass
                def log_memory_injector_keywords(self, *args): pass
                def log_collective_wisdom_search(self, *args): pass
                def log_collective_wisdom_results(self, *args): pass
                def log_relevance_calculation(self, *args): pass
                def log_memory_chunks_selection(self, *args): pass
                def log_memory_chunk_details(self, *args): pass
                def log_no_memory_injection(self, *args): pass
                def log_memory_injection_result(self, *args): pass
                def log_error(self, *args): pass
            def get_memory_debug_logger():
                return DummyLogger()
        debug_logger = get_memory_debug_logger()
        debug_logger.log_memory_injector_start(query, context, user_id)
        
        if not self.collective_mind:
            debug_logger.log_no_memory_injection("collective_mind not available")
            return []
        
        # Извлекаем ключевые слова
        query_keywords = self.extract_keywords(query)
        context_keywords = self.extract_keywords(context)
        debug_logger.log_memory_injector_keywords(query_keywords, context_keywords)
        
        # Получаем потенциально релевантные воспоминания
        all_memories = []
        
        # 🔒 ИСПРАВЛЕНИЕ: Сначала ищем в коллективной памяти, потом в персональной
        # Поиск по ключевым словам в коллективной памяти (общие знания)
        for keyword in query_keywords[:3]:  # Уменьшили с 5 до 3
            try:
                debug_logger.log_collective_wisdom_search(keyword, 10)
                memories = await self.collective_mind.get_collective_wisdom(
                    keyword, limit=10  # Уменьшили с 20 до 10
                )
                
                # Проверяем, что memories не None и является списком
                if memories and isinstance(memories, list):
                    debug_logger.log_collective_wisdom_results(keyword, len(memories), memories)
                    
                    # Фильтруем слишком старые записи (старше 90 дней)
                    current_time = time.time()
                    fresh_memories = [
                        memory for memory in memories 
                        if hasattr(memory, 'timestamp') and (current_time - memory.timestamp) < (90 * 24 * 60 * 60)  # 90 дней
                    ]
                    all_memories.extend(fresh_memories)
                else:
                    logger.debug(f"Пустой результат для ключевого слова: {keyword}")
                    
            except Exception as e:
                logger.warning(f"Ошибка поиска коллективной мудрости для '{keyword}': {e}")
                continue
        
        # 🔒 ИСПРАВЛЕНИЕ: Добавляем поиск в персональной памяти если указан user_id
        if user_id and len(all_memories) < 5:  # Если мало коллективных воспоминаний
            try:
                from memory.lazy_memory import get_lazy_memory
                lazy_memory = get_lazy_memory()
                if lazy_memory:
                    personal_memories = lazy_memory.get_relevant_history(user_id, query, limit=10)
                    for memory in personal_memories:
                        # Создаем MemoryChunk из персональной памяти
                        chunk = MemoryChunk(
                            id=f"personal_{user_id}_{hash(memory['content'])}",  # Уникальный ID
                            content=memory['content'],
                            relevance_score=0.8,  # Высокая релевантность для персональной памяти
                            memory_type='personal',
                            source_agent=user_id,
                            importance=0.9,
                            tokens_count=self.count_tokens(memory['content']),
                            context_tags=[],
                            timestamp=memory.get('timestamp', time.time())
                        )
                        all_memories.append(chunk)
            except Exception as e:
                logger.warning(f"Ошибка поиска персональной памяти для {user_id}: {e}")
        
        # Удаляем дубликаты
        unique_memories = {}
        for memory in all_memories:
            if memory.id not in unique_memories:
                unique_memories[memory.id] = memory
        
        # Создаем чанки с релевантностью
        memory_chunks = []
        for memory in unique_memories.values():
            relevance = self.calculate_relevance(memory, query_keywords, context_keywords)
            debug_logger.log_relevance_calculation(memory.id, relevance, self.min_relevance_threshold)
            
            if relevance > self.min_relevance_threshold:  # Повышенный порог релевантности
                chunk = MemoryChunk(
                    id=memory.id,
                    content=memory.content,
                    relevance_score=relevance,
                    memory_type=memory.memory_type,
                    source_agent=memory.agent_id,
                    importance=memory.importance,
                    tokens_count=self.count_tokens(memory.content),
                    context_tags=getattr(memory, 'tags', []),
                    timestamp=memory.timestamp
                )
                memory_chunks.append(chunk)
        
        # Сортируем по релевантности
        memory_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        final_chunks = memory_chunks[:max_memories]
        
        debug_logger.log_memory_chunks_selection(len(memory_chunks), len(final_chunks), 0)
        
        # Логируем детали выбранных чанков
        for i, chunk in enumerate(final_chunks):
            debug_logger.log_memory_chunk_details(
                i, chunk.memory_type, chunk.relevance_score, 
                chunk.tokens_count, chunk.content
            )
        
        return final_chunks
    
    def optimize_memory_selection(self, memory_chunks: List[MemoryChunk], 
                                 available_tokens: int) -> List[MemoryChunk]:
        """Оптимизация выбора памяти под бюджет токенов"""
        if not memory_chunks:
            return []
        
        # Алгоритм рюкзака для оптимального выбора
        selected_chunks = []
        used_tokens = 0
        
        # Сортируем по отношению релевантности к размеру
        efficiency_sorted = sorted(
            memory_chunks, 
            key=lambda x: x.relevance_score / max(x.tokens_count, 1), 
            reverse=True
        )
        
        for chunk in efficiency_sorted:
            if used_tokens + chunk.tokens_count <= available_tokens:
                selected_chunks.append(chunk)
                used_tokens += chunk.tokens_count
            else:
                # Пытаемся урезать чанк
                remaining_tokens = available_tokens - used_tokens
                if remaining_tokens > 50:  # Минимальный размер чанка
                    truncated_content = self.truncate_content(
                        chunk.content, remaining_tokens
                    )
                    if truncated_content:
                        truncated_chunk = MemoryChunk(
                            content=truncated_content,
                            relevance_score=chunk.relevance_score * 0.8,  # Штраф за урезание
                            memory_type=chunk.memory_type,
                            source_agent=chunk.source_agent,
                            importance=chunk.importance,
                            tokens_count=remaining_tokens,
                            context_tags=chunk.context_tags,
                            timestamp=chunk.timestamp
                        )
                        selected_chunks.append(truncated_chunk)
                        used_tokens = available_tokens
                break
        
        return selected_chunks
    
    def truncate_content(self, content: str, max_tokens: int) -> str:
        """Умное урезание контента с сохранением смысла"""
        if self.count_tokens(content) <= max_tokens:
            return content
        
        # Разбиваем на предложения
        sentences = re.split(r'[.!?]+', content)
        
        result = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            test_content = result + sentence + ". "
            if self.count_tokens(test_content) <= max_tokens - 10:  # Запас
                result = test_content
            else:
                break
        
        # Если результат слишком короткий, берем первые токены
        if len(result) < 50:
            tokens = self.tokenizer.encode(content)[:max_tokens-1]
            result = self.tokenizer.decode(tokens)
        
        return result.strip()
    
    def format_memory_injection(self, memory_chunks: List[MemoryChunk]) -> str:
        """Форматирование памяти для инъекции в промпт"""
        if not memory_chunks:
            return ""
        
        # Группируем по типам памяти
        memory_groups = defaultdict(list)
        for chunk in memory_chunks:
            memory_groups[chunk.memory_type].append(chunk)
        
        formatted_sections = []
        
        for memory_type, chunks in memory_groups.items():
            if not chunks:
                continue
                
            # Заголовок секции
            type_names = {
                'insight': 'Коллективные инсайты',
                'wisdom': 'Мудрость сети',
                'experience': 'Опыт агентов',
                'observation': 'Наблюдения',
                'reflection': 'Размышления'
            }
            
            section_title = type_names.get(memory_type, 'Память сети')
            section_content = f"\n=== {section_title} ===\n"
            
            # Добавляем воспоминания
            for i, chunk in enumerate(chunks, 1):
                relevance_stars = "⭐" * min(int(chunk.relevance_score * 5), 5)
                section_content += f"\n{i}. {relevance_stars} (Релевантность: {chunk.relevance_score:.2f})\n"
                section_content += f"   {chunk.content}\n"
                
                # Добавляем метаданные для важных воспоминаний
                if chunk.importance > 0.8:
                    section_content += f"   [Источник: {chunk.source_agent[:8]}..., Важность: {chunk.importance:.2f}]\n"
            
            formatted_sections.append(section_content)
        
        # Объединяем все секции
        memory_injection = "\n".join(formatted_sections)
        
        # Добавляем инструкцию по использованию
        instruction = """
=== Инструкция по использованию коллективной памяти ===
Выше представлена релевантная информация из коллективной памяти сети AI-агентов.
Используй эти знания для:
- Обогащения своих ответов проверенным опытом
- Избежания повторения ошибок других агентов
- Применения успешных паттернов и стратегий
- Создания более глубоких и обоснованных суждений

Помни: коллективная память - это не абсолютная истина, а накопленный опыт.
Критически оценивай информацию и адаптируй её под текущий контекст.
"""
        
        return instruction + memory_injection
    
    async def inject_memory_into_prompt(self, original_prompt: str, 
                                      context: str = "", 
                                      user_id: str = None,
                                      memory_budget_ratio: float = None) -> str:
        """Главная функция инъекции памяти в промпт"""
        # Логирование отладки памяти
        try:
            import sys
            sys.path.append('backend')
            from utils.memory_debug_logger import get_memory_debug_logger
        except ImportError:
            # Fallback - создаем заглушку
            class DummyLogger:
                def log_memory_injector_start(self, *args): pass
                def log_memory_injector_keywords(self, *args): pass
                def log_collective_wisdom_search(self, *args): pass
                def log_collective_wisdom_results(self, *args): pass
                def log_relevance_calculation(self, *args): pass
                def log_memory_chunks_selection(self, *args): pass
                def log_memory_chunk_details(self, *args): pass
                def log_no_memory_injection(self, *args): pass
                def log_memory_injection_result(self, *args): pass
                def log_error(self, *args): pass
            def get_memory_debug_logger():
                return DummyLogger()
        debug_logger = get_memory_debug_logger()
        
        try:
            # Определяем бюджет токенов для памяти
            if memory_budget_ratio:
                memory_tokens = int(self.max_context_tokens * memory_budget_ratio)
            else:
                memory_tokens = self.max_memory_tokens
            
            # Подсчитываем токены исходного промпта
            original_tokens = self.count_tokens(original_prompt)
            context_tokens = self.count_tokens(context)
            
            # Доступные токены для памяти
            available_tokens = memory_tokens - 500  # Запас на форматирование
            
            if available_tokens < 100:
                debug_logger.log_no_memory_injection(f"insufficient tokens: {available_tokens}")
                logger.warning("Недостаточно токенов для инъекции памяти")
                return original_prompt
            
            # 🔒 ИСПРАВЛЕНИЕ: Передаем user_id для фильтрации памяти
            memory_chunks = await self.select_relevant_memories(
                original_prompt, context, user_id
            )
            
            if not memory_chunks:
                debug_logger.log_no_memory_injection("no relevant memories found")
                logger.info("Релевантные воспоминания не найдены")
                return original_prompt
            
            # Оптимизируем выбор под бюджет токенов
            selected_chunks = self.optimize_memory_selection(
                memory_chunks, available_tokens
            )
            
            if not selected_chunks:
                debug_logger.log_no_memory_injection("no suitable chunks after optimization")
                logger.warning("Не удалось выбрать воспоминания под бюджет токенов")
                return original_prompt
            
            # Форматируем память для инъекции
            memory_injection = self.format_memory_injection(selected_chunks)
            
            # Создаем итоговый промпт
            enhanced_prompt = f"""{memory_injection}

=== Основной запрос ===
{original_prompt}

=== Контекст ===
{context}

Используй коллективную память для создания максимально качественного ответа."""
            
            # Проверяем итоговый размер
            total_tokens = self.count_tokens(enhanced_prompt)
            original_tokens = self.count_tokens(original_prompt)
            injected_tokens = total_tokens - original_tokens
            
            debug_logger.log_memory_injection_result(original_tokens, injected_tokens, len(selected_chunks))
            
            logger.info(f"Инъекция памяти: {len(selected_chunks)} чанков, "
                       f"{total_tokens} токенов, "
                       f"релевантность: {selected_chunks[0].relevance_score:.2f}")
            
            return enhanced_prompt
            
        except Exception as e:
            debug_logger.log_error("memory_injector", e, {"prompt_length": len(original_prompt)})
            logger.error(f"Ошибка инъекции памяти: {e}")
            return original_prompt
    
    async def analyze_memory_usage(self, prompt: str, user_id: str = None) -> Dict[str, Any]:
        """Анализ использования памяти в промпте"""
        try:
            # Проверяем, что collective_mind доступен
            if not self.collective_mind:
                logger.debug("collective_mind недоступен для анализа")
                return {
                    'total_available': 0,
                    'relevance_distribution': {},
                    'type_distribution': {},
                    'token_usage': 0,
                    'error': 'collective_mind_not_available'
                }
            
            memory_chunks = await self.select_relevant_memories(prompt, "", user_id)
            
            if not memory_chunks:
                return {
                    'total_available': 0,
                    'relevance_distribution': {},
                    'type_distribution': {},
                    'token_usage': 0
                }
            
            # Анализируем распределение релевантности
            relevance_ranges = {
                'high': len([c for c in memory_chunks if c.relevance_score > 0.7]),
                'medium': len([c for c in memory_chunks if 0.3 < c.relevance_score <= 0.7]),
                'low': len([c for c in memory_chunks if c.relevance_score <= 0.3])
            }
            
            # Анализируем типы памяти
            type_counts = defaultdict(int)
            for chunk in memory_chunks:
                type_counts[chunk.memory_type] += 1
            
            # Подсчитываем токены
            total_tokens = sum(chunk.tokens_count for chunk in memory_chunks)
            
            return {
                'total_available': len(memory_chunks),
                'relevance_distribution': relevance_ranges,
                'type_distribution': dict(type_counts),
                'token_usage': total_tokens,
                'top_relevance': memory_chunks[0].relevance_score if memory_chunks else 0,
                'memory_efficiency': len(memory_chunks) / max(total_tokens, 1) * 1000
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа памяти: {e}")
            return {
                'total_available': 0,
                'relevance_distribution': {},
                'type_distribution': {},
                'token_usage': 0,
                'error': str(e)
            }


# Глобальный экземпляр инжектора
memory_injector = None

def get_memory_injector() -> MemoryInjector:
    """Получение экземпляра инжектора памяти"""
    global memory_injector
    if memory_injector is None:
        memory_injector = MemoryInjector()
    return memory_injector


async def enhance_prompt_with_memory(prompt: str, context: str = "", 
                                   user_id: str = None,
                                   memory_budget: float = 0.3) -> str:
    """Упрощенная функция для улучшения промпта коллективной памятью"""
    injector = get_memory_injector()
    return await injector.inject_memory_into_prompt(prompt, context, user_id, memory_budget)


async def analyze_prompt_memory_potential(prompt: str) -> Dict[str, Any]:
    """Анализ потенциала использования памяти для промпта"""
    injector = get_memory_injector()
    return await injector.analyze_memory_usage(prompt) 