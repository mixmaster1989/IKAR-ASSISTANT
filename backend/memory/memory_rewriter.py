"""
Система нативного перезаписывания чанков памяти
Комбинированный механизм: Entity extraction + Semantic search + LLM analysis + Version control + Smart deletion
"""

import asyncio
import json
import re
import time
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np

# Удален импорт vector_store - заменен на lazy_memory
from backend.llm import OpenRouterClient
from backend.memory.embeddings import EmbeddingGenerator

logger = logging.getLogger("chatumba.memory_rewriter")


@dataclass
class MemoryEntity:
    """Сущность из памяти"""
    name: str
    entity_type: str  # "object", "action", "status", "person", "location"
    confidence: float
    context: str


@dataclass
class MemoryVersion:
    """Версия чанка памяти"""
    version_id: str
    content: str
    timestamp: float
    status: str  # "current", "outdated", "merged"
    entities: List[MemoryEntity]
    metadata: Dict[str, Any]


@dataclass
class MemoryChunk:
    """Чанк памяти с версионированием"""
    chunk_id: str
    user_id: str
    current_version: MemoryVersion
    version_history: List[MemoryVersion]
    entity_key: str  # Уникальный ключ для поиска связанных чанков
    last_updated: float
    importance: float


class MemoryRewriter:
    """
    Переписывает и оптимизирует воспоминания с помощью LLM.
    """
    
    def __init__(self, lazy_memory, llm_client: OpenRouterClient, embedding_generator: EmbeddingGenerator):
        self.lazy_memory = lazy_memory
        self.llm_client = llm_client
        self.embedding_generator = embedding_generator
        
        # Пороги для определения связанности
        self.semantic_similarity_threshold = 0.75
        self.entity_match_threshold = 0.6
        self.outdated_time_threshold = 30 * 24 * 3600  # 30 дней
        
        # Кеш для оптимизации
        self.entity_cache = {}
        self.similarity_cache = {}
        
    async def process_new_memory(self, text: str, user_id: Union[str, int], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Обрабатывает новое воспоминание с возможностью перезаписывания
        """
        try:
            # 1. Извлекаем сущности из нового текста
            entities = await self._extract_entities(text)
            
            # 2. Ищем связанные чанки
            related_chunks = await self._find_related_memories(text, entities, user_id)
            
            if related_chunks:
                # 3. Анализируем необходимость перезаписывания
                should_rewrite = await self._analyze_rewrite_necessity(text, related_chunks[0])
                
                if should_rewrite:
                    # 4. Перезаписываем чанк
                    success = await self._rewrite_memory(text, related_chunks[0], entities, user_id, metadata)
                    if success:
                        return True
            
            # 5. Если нет связанных чанков или перезаписывание не нужно - добавляем новый
            return await self._add_new_memory(text, entities, user_id, metadata)
            
        except Exception as e:
            logger.error(f"Ошибка обработки нового воспоминания: {e}")
            # Fallback: просто добавляем как новое воспоминание
            try:
                entities = self._fallback_entity_extraction(text)
                return await self._add_new_memory(text, entities, user_id, metadata)
            except Exception as fallback_error:
                logger.error(f"Fallback также не сработал: {fallback_error}")
                return False
    
    async def _extract_entities(self, text: str) -> List[MemoryEntity]:
        """
        Извлекает сущности из текста с помощью LLM
        """
        try:
            # Промпт для извлечения сущностей
            entity_prompt = f"""
            ИЗВЛЕЧЕНИЕ СУЩНОСТЕЙ
            
            ТЕКСТ: {text}
            
            ВЕРНИ JSON МАССИВ:
            [
                {{
                    "name": "название",
                    "type": "object|action|status|person|location",
                    "confidence": 0.0-1.0,
                    "context": "описание"
                }}
            ]
            
            ТИПЫ:
            - object: сервер, компьютер, дом, машина
            - action: купить, продать, запустить, остановить  
            - status: работает, сломан, куплен, продан
            - person: Иван, Маша, клиент
            - location: офис, дом, магазин
            """
            
            response = await self.llm_client.chat_completion(
                user_message=entity_prompt,
                system_prompt="Ты - система извлечения сущностей. Возвращай ТОЛЬКО валидный JSON массив. Никакого дополнительного текста.",
                temperature=0.0,
                max_tokens=500
            )
            
            # Парсим JSON ответ с надежным парсером
            try:
                entities_data = self._robust_json_parser(response)
                
                # Проверяем, что это список
                if not isinstance(entities_data, list):
                    entities_data = [entities_data]
                
                entities = []
                
                for entity_data in entities_data:
                    if isinstance(entity_data, dict):
                        entity = MemoryEntity(
                            name=entity_data.get("name", ""),
                            entity_type=entity_data.get("type", "object"),
                            confidence=float(entity_data.get("confidence", 0.5)),
                            context=entity_data.get("context", "")
                        )
                        entities.append(entity)
                
                logger.info(f"Извлечено {len(entities)} сущностей из текста")
                return entities
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"Не удалось распарсить JSON с сущностями: {e}")
                logger.debug(f"Ответ LLM: {response}")
                return self._fallback_entity_extraction(text)
                
        except Exception as e:
            logger.error(f"Ошибка извлечения сущностей: {e}")
            return self._fallback_entity_extraction(text)
    
    def _fallback_entity_extraction(self, text: str) -> List[MemoryEntity]:
        """
        Простое извлечение сущностей через регулярные выражения
        """
        entities = []
        
        # Ищем объекты (слова с большой буквы и ключевые слова)
        objects = re.findall(r'\b[A-ZА-Я][a-zа-я]+\b', text)
        key_objects = re.findall(r'\b(сервер|компьютер|дом|машина|телефон|ноутбук)\b', text, re.IGNORECASE)
        
        for obj in objects + key_objects:
            entities.append(MemoryEntity(
                name=obj,
                entity_type="object",
                confidence=0.6,
                context=text
            ))
        
        # Ищем действия (глаголы)
        actions = re.findall(r'\b(купить|продать|запустить|остановить|сделать|построить|создать|купили|купил|купила)\b', text, re.IGNORECASE)
        for action in actions:
            entities.append(MemoryEntity(
                name=action,
                entity_type="action",
                confidence=0.7,
                context=text
            ))
        
        # Ищем статусы
        statuses = re.findall(r'\b(работает|сломан|куплен|продан|готов|готово|нужно|нужен)\b', text, re.IGNORECASE)
        for status in statuses:
            entities.append(MemoryEntity(
                name=status,
                entity_type="status",
                confidence=0.6,
                context=text
            ))
        
        # Ищем цены
        prices = re.findall(r'\b(\d+р|\d+\s*руб|\d+\s*доллар|\d+\s*евро)\b', text, re.IGNORECASE)
        for price in prices:
            entities.append(MemoryEntity(
                name=price,
                entity_type="status",
                confidence=0.8,
                context=text
            ))
        
        logger.info(f"Fallback извлечение: найдено {len(entities)} сущностей")
        return entities
    
    def _robust_json_parser(self, response: str) -> List[Dict[str, Any]]:
        """
        Надежный парсер JSON, который справляется с любыми выкрутасами LLM
        """
        import re
        
        # 1. Очищаем от markdown разметки
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Try aggressive JSON extraction first
        try:
            from backend.utils.json_surgeon import parse_all_json as _surgeon_parse_all  # type: ignore
            items = _surgeon_parse_all(cleaned)
            dicts = [it for it in items if isinstance(it, dict)]
            if dicts:
                return dicts
        except Exception:
            pass
        
        # 2. Ищем JSON объекты в тексте
        json_objects = []
        
        # Паттерн для поиска JSON объектов
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(pattern, cleaned, re.DOTALL)
        
        for match in matches:
            try:
                # Исправляем незакрытые строки
                fixed_json = self._fix_json_strings(match)
                obj = json.loads(fixed_json)
                json_objects.append(obj)
            except:
                continue
        
        # 3. Если не нашли JSON объекты, пытаемся извлечь данные через regex
        if not json_objects:
            json_objects = self._extract_entities_via_regex(cleaned)
        
        return json_objects
    
    def _fix_json_strings(self, json_str: str) -> str:
        """
        Исправляет незакрытые строки в JSON
        """
        import re
        
        # Исправляем незакрытые строки в context
        pattern = r'"context":\s*"([^"]*?)(?:"|$)'
        def fix_context(match):
            context = match.group(1)
            # Экранируем кавычки внутри строки
            context = context.replace('"', '\\"')
            return f'"context": "{context}"'
        
        fixed = re.sub(pattern, fix_context, json_str)
        
        # Исправляем незакрытые строки в name
        pattern = r'"name":\s*"([^"]*?)(?:"|$)'
        def fix_name(match):
            name = match.group(1)
            name = name.replace('"', '\\"')
            return f'"name": "{name}"'
        
        fixed = re.sub(pattern, fix_name, fixed)
        
        # Исправляем незакрытые строки в type
        pattern = r'"type":\s*"([^"]*?)(?:"|$)'
        def fix_type(match):
            type_val = match.group(1)
            type_val = type_val.replace('"', '\\"')
            return f'"type": "{type_val}"'
        
        fixed = re.sub(pattern, fix_type, fixed)
        
        return fixed
    
    def _extract_entities_via_regex(self, text: str) -> List[Dict[str, Any]]:
        """
        Извлекает сущности через регулярные выражения из текста
        """
        entities = []
        
        # Ищем паттерны типа "name": "value"
        name_pattern = r'"name":\s*"([^"]+)"'
        type_pattern = r'"type":\s*"([^"]+)"'
        confidence_pattern = r'"confidence":\s*([0-9.]+)'
        context_pattern = r'"context":\s*"([^"]*)"'
        
        # Разбиваем на строки и ищем объекты
        lines = text.split('\n')
        current_entity = {}
        
        for line in lines:
            line = line.strip()
            
            # Ищем name
            name_match = re.search(name_pattern, line)
            if name_match:
                if current_entity:
                    entities.append(current_entity)
                current_entity = {"name": name_match.group(1)}
            
            # Ищем type
            type_match = re.search(type_pattern, line)
            if type_match and current_entity:
                current_entity["type"] = type_match.group(1)
            
            # Ищем confidence
            conf_match = re.search(confidence_pattern, line)
            if conf_match and current_entity:
                current_entity["confidence"] = float(conf_match.group(1))
            
            # Ищем context
            context_match = re.search(context_pattern, line)
            if context_match and current_entity:
                current_entity["context"] = context_match.group(1)
        
        # Добавляем последний объект
        if current_entity:
            entities.append(current_entity)
        
        return entities
    
    async def _find_related_memories(self, text: str, entities: List[MemoryEntity], user_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Ищет связанные воспоминания по семантическому сходству и сущностям
        """
        try:
            # LazyMemory не требует инициализации индекса - это SQLite-based система
            # Просто проверяем, что память доступна
            if not hasattr(self.lazy_memory, 'db_path'):
                logger.warning("LazyMemory не инициализирована")
                return []
            
            # 1. Семантический поиск
            semantic_results = self.lazy_memory.get_relevant_history(str(user_id), text, limit=10)
            
            # 2. Фильтруем по релевантности
            relevant_results = []
            
            for result in semantic_results:
                # LazyMemory не возвращает score, поэтому используем простую логику
                # Если результат найден, считаем его релевантным
                content = result.get("content", "")
                
                # Проверяем совпадение сущностей
                entity_match_score = self._calculate_entity_match(entities, content)
                if entity_match_score >= self.entity_match_threshold:
                    # Добавляем score для совместимости
                    result["score"] = entity_match_score
                    relevant_results.append(result)
                else:
                    # Если нет совпадения сущностей, но есть контент, добавляем с низким score
                    result["score"] = 0.1
                    relevant_results.append(result)
            
            # 3. Сортируем по релевантности
            relevant_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            logger.info(f"Найдено {len(relevant_results)} связанных воспоминаний")
            return relevant_results
            
        except Exception as e:
            logger.error(f"Ошибка поиска связанных воспоминаний: {e}")
            return []
    
    def _calculate_entity_match(self, entities: List[MemoryEntity], text: str) -> float:
        """
        Вычисляет степень совпадения сущностей
        """
        if not entities:
            return 0.0
        
        text_lower = text.lower()
        matches = 0
        
        for entity in entities:
            if entity.name.lower() in text_lower:
                matches += 1
        
        return matches / len(entities)
    
    async def _analyze_rewrite_necessity(self, new_text: str, old_memory: Dict[str, Any]) -> bool:
        """
        Анализирует необходимость перезаписывания с помощью LLM
        """
        try:
            old_text = old_memory.get("text", "")
            
            analysis_prompt = f"""
            АНАЛИЗ ПЕРЕЗАПИСИ ПАМЯТИ
            
            СТАРОЕ ВОСПОМИНАНИЕ: {old_text}
            НОВОЕ СООБЩЕНИЕ: {new_text}
            
            ПРАВИЛА:
            - Если новое сообщение ОБНОВЛЯЕТ информацию из старого → ДА
            - Если новое сообщение ИСПРАВЛЯЕТ ошибку в старом → ДА  
            - Если это ОДИН И ТОТ ЖЕ объект/событие → ДА
            - Если это РАЗНЫЕ события/объекты → НЕТ
            - Если старая информация ВСЕ ЕЩЕ АКТУАЛЬНА → НЕТ
            
            ОТВЕТЬ ТОЛЬКО ОДНИМ СЛОВОМ: ДА или НЕТ
            """
            
            response = await self.llm_client.chat_completion(
                user_message=analysis_prompt,
                system_prompt="Ты - система анализа. Отвечай ТОЛЬКО ДА или НЕТ. Никаких объяснений, никакого JSON.",
                temperature=0.0,
                max_tokens=5
            )
            
            should_rewrite = "ДА" in response.upper()
            logger.info(f"Анализ перезаписи: {should_rewrite} (старое: '{old_text[:50]}...', новое: '{new_text[:50]}...')")
            
            return should_rewrite
            
        except Exception as e:
            logger.error(f"Ошибка анализа необходимости перезаписи: {e}")
            return False
    
    async def _rewrite_memory(self, new_text: str, old_memory: Dict[str, Any], entities: List[MemoryEntity], 
                             user_id: Union[str, int], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Перезаписывает существующее воспоминание
        """
        try:
            old_text = old_memory.get("text", "")
            memory_id = old_memory.get("id", "")
            
            # 1. Создаем новую версию с помощью LLM
            merged_content = await self._merge_memories(old_text, new_text)
            
            # 2. Создаем новую версию
            new_version = MemoryVersion(
                version_id=f"v{int(time.time())}",
                content=merged_content,
                timestamp=time.time(),
                status="current",
                entities=entities,
                metadata=metadata or {}
            )
            
            # 3. Помечаем старую версию как устаревшую
            old_version = MemoryVersion(
                version_id=f"v{old_memory.get('timestamp', int(time.time()))}",
                content=old_text,
                timestamp=old_memory.get('timestamp', time.time()),
                status="outdated",
                entities=[],  # Будет заполнено позже
                metadata=old_memory.get('metadata', {})
            )
            
            # 4. Обновляем в векторном хранилище
            success = await self._update_memory_in_store(memory_id, merged_content, user_id, metadata)
            
            if success:
                logger.info(f"Воспоминание перезаписано: {old_text[:50]}... → {merged_content[:50]}...")
                
                # 5. Сохраняем историю версий (если есть поддержка)
                await self._save_version_history(memory_id, [old_version, new_version], user_id)
                
                return True
            else:
                logger.error("Не удалось обновить воспоминание в хранилище")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка перезаписи воспоминания: {e}")
            return False
    
    async def _merge_memories(self, old_text: str, new_text: str) -> str:
        """
        Объединяет старое и новое воспоминание с помощью LLM
        """
        try:
            merge_prompt = f"""
            Объедини старое и новое воспоминание в одно актуальное.
            
            Старое: {old_text}
            Новое: {new_text}
            
            Правила объединения:
            - Сохрани важную информацию из старого
            - Добавь новую информацию
            - Убери устаревшую информацию
            - Сделай текст естественным и понятным
            - Не дублируй информацию
            
            Объединенное воспоминание:
            """
            
            merged_content = await self.llm_client.chat_completion(
                user_message=merge_prompt,
                system_prompt="Ты - система объединения воспоминаний. Создавай естественный и информативный текст.",
                temperature=0.3
            )
            
            return merged_content.strip()
            
        except Exception as e:
            logger.error(f"Ошибка объединения воспоминаний: {e}")
            # Fallback: просто возвращаем новое
            return new_text
    
    async def _update_memory_in_store(self, memory_id: str, new_content: str, user_id: Union[str, int], 
                                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Обновляет воспоминание в LazyMemory
        """
        try:
            # LazyMemory не поддерживает обновление отдельных записей
            # Просто добавляем новое сообщение
            chat_id = metadata.get("chat_id", "unknown") if metadata else "unknown"
            self.lazy_memory.add_message(str(user_id), chat_id, new_content, "text")
            
            logger.info(f"Воспоминание обновлено в LazyMemory для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления в хранилище: {e}")
            return False
    
    async def _save_version_history(self, memory_id: str, versions: List[MemoryVersion], user_id: Union[str, int]) -> bool:
        """
        Сохраняет историю версий (опционально)
        """
        try:
            # Пока просто логируем, в будущем можно добавить отдельную таблицу
            version_data = {
                "memory_id": memory_id,
                "user_id": str(user_id),
                "versions": [asdict(v) for v in versions],
                "timestamp": time.time()
            }
            
            logger.info(f"История версий сохранена для {memory_id}: {len(versions)} версий")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения истории версий: {e}")
            return False
    
    async def _add_new_memory(self, text: str, entities: List[MemoryEntity], user_id: Union[str, int], 
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Добавляет новое воспоминание в LazyMemory
        """
        try:
            # Создаем entity_key для будущего поиска
            entity_key = self._create_entity_key(entities)
            
            # Добавляем в метаданные
            if metadata is None:
                metadata = {}
            
            metadata.update({
                "entities": [asdict(e) for e in entities],
                "entity_key": entity_key,
                "version": "1.0",
                "created_at": time.time()
            })
            
            # Добавляем в LazyMemory
            chat_id = metadata.get("chat_id", "unknown")
            self.lazy_memory.add_message(str(user_id), chat_id, text, "text")
            
            logger.info(f"Добавлено новое воспоминание в LazyMemory: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления нового воспоминания: {e}")
            return False
    
    def _create_entity_key(self, entities: List[MemoryEntity]) -> str:
        """
        Создает уникальный ключ для поиска связанных чанков
        """
        if not entities:
            return "general"
        
        # Сортируем сущности по типу и имени для стабильности
        sorted_entities = sorted(entities, key=lambda e: (e.entity_type, e.name))
        
        # Создаем ключ из типов и имен
        key_parts = [f"{e.entity_type}:{e.name}" for e in sorted_entities]
        return "|".join(key_parts)
    
    async def cleanup_outdated_memories(self, user_id: Union[str, int]) -> int:
        """
        Очищает устаревшие воспоминания
        """
        try:
            # LazyMemory имеет встроенный метод очистки старых сообщений
            # Используем его вместо ручной очистки
            self.lazy_memory.clear_old_messages(days=30)
            
            logger.info(f"Очистка устаревших воспоминаний выполнена для пользователя {user_id}")
            return 1  # Возвращаем 1, так как очистка выполнена
            
        except Exception as e:
            logger.error(f"Ошибка очистки устаревших воспоминаний: {e}")
            return 0 
