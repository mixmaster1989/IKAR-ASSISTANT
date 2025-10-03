"""
API для управления системой инъекции коллективной памяти
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
from datetime import datetime
from backend.core.memory_injector import get_memory_injector
from backend.llm import get_openrouter_client
from backend.utils.logger import get_logger
from backend.config import Config

# Получаем логгер для этого модуля
logger = get_logger('memory_api')

memory_router = APIRouter(tags=["Memory System"])

# Модели данных для API
class PromptEnhanceModel(BaseModel):
    prompt: str
    context: str = ""
    memory_budget: float = 0.3

class PromptAnalyzeModel(BaseModel):
    prompt: str

class GenerateWithAnalysisModel(BaseModel):
    prompt: str
    context: str = ""
    use_memory: bool = True
    memory_budget: float = 0.3

class MemoryConfigModel(BaseModel):
    memory_budget_ratio: Optional[float] = None
    importance_threshold: Optional[float] = None
    max_memory_tokens: Optional[int] = None
    memory_type_weights: Optional[Dict[str, float]] = None

class MemoryOptimizeModel(BaseModel):
    prompt: str
    available_memories: List[Dict[str, Any]]
    token_budget: int


@memory_router.post('/memory/enhance_prompt')
async def enhance_prompt(data: PromptEnhanceModel):
    """Улучшение промпта коллективной памятью"""
    try:
        # Асинхронное улучшение промпта
        injector = get_memory_injector()
        enhanced_prompt = await injector.inject_memory_into_prompt(
            data.prompt, data.context, data.memory_budget
        )
        
        # Анализ использования памяти
        memory_analysis = await injector.analyze_memory_usage(data.prompt)
        
        return {
            'original_prompt': data.prompt,
            'enhanced_prompt': enhanced_prompt,
            'memory_analysis': memory_analysis,
            'enhancement_applied': len(enhanced_prompt) > len(data.prompt),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка улучшения промпта: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.post('/memory/analyze_prompt')
async def analyze_prompt(data: PromptAnalyzeModel):
    """Анализ потенциала использования памяти для промпта"""
    try:
        # Асинхронный анализ
        injector = get_memory_injector()
        analysis = await injector.analyze_memory_usage(data.prompt)
        
        return {
            'prompt': data.prompt,
            'analysis': analysis,
            'recommendations': {
                'use_memory': analysis.get('total_available', 0) > 0,
                'optimal_budget': 0.3 if analysis.get('total_available', 0) > 5 else 0.2,
                'expected_enhancement': 'high' if analysis.get('top_relevance', 0) > 0.7 else 'medium'
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка анализа промпта: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.post('/memory/generate_with_analysis')
async def generate_with_analysis(data: GenerateWithAnalysisModel):
    """Генерация ответа с подробным анализом использования памяти"""
    try:
        # Получение клиента
        config = Config()
        client = get_openrouter_client(config)
        
        if not client:
            raise HTTPException(status_code=503, detail='OpenRouter клиент не инициализирован')
        
        # Асинхронная генерация с анализом
        if data.use_memory:
            result = await client.generate_with_memory_analysis(data.prompt, data.context)
        else:
            response = await client.generate_response(data.prompt, data.context, use_memory=False)
            result = {
                'response': response,
                'memory_analysis': {},
                'generation_time': 0,
                'memory_used': False,
                'memory_efficiency': 0
            }
        
        return {
            'prompt': data.prompt,
            'response': result['response'],
            'memory_analysis': result['memory_analysis'],
            'generation_time': result['generation_time'],
            'memory_used': result['memory_used'],
            'memory_efficiency': result['memory_efficiency'],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка генерации с анализом: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.get('/memory/stats')
async def get_memory_stats():
    """Статистика использования системы инъекции памяти"""
    try:
        config = Config()
        client = get_openrouter_client(config)
        
        if not client:
            raise HTTPException(status_code=503, detail='OpenRouter клиент не инициализирован')
        
        # Статистика клиента
        client_stats = client.get_memory_stats()
        
        # Статистика инжектора
        injector = get_memory_injector()
        
        return {
            'client_stats': client_stats,
            'injector_config': {
                'max_context_tokens': injector.max_context_tokens,
                'memory_budget_ratio': injector.memory_budget_ratio,
                'max_memory_tokens': injector.max_memory_tokens
            },
            'cache_stats': {
                'relevance_cache_size': len(injector.relevance_cache),
                'token_cache_size': len(injector.token_cache)
            },
            'memory_type_weights': injector.memory_type_weights,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.post('/memory/test_integration')
async def test_memory_integration(data: PromptAnalyzeModel):
    """Тестирование интеграции системы памяти"""
    try:
        test_prompt = data.prompt or 'Расскажи о важности коллективного разума'
        
        # Получение клиента
        config = Config()
        client = get_openrouter_client(config)
        
        if not client:
            raise HTTPException(status_code=503, detail='OpenRouter клиент не инициализирован')
        
        # Тестирование A/B
        response_with_memory = await client.generate_response(test_prompt, use_memory=True)
        response_without_memory = await client.generate_response(test_prompt, use_memory=False)
        
        # Анализ памяти
        injector = get_memory_injector()
        memory_analysis = await injector.analyze_memory_usage(test_prompt)
        
        # Статистика
        stats = client.get_memory_stats()
        
        return {
            'test_prompt': test_prompt,
            'response_with_memory': response_with_memory,
            'response_without_memory': response_without_memory,
            'memory_analysis': memory_analysis,
            'performance_stats': stats,
            'integration_status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка тестирования: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.post('/memory/configure')
async def configure_memory(config: MemoryConfigModel):
    """Настройка параметров системы памяти"""
    try:
        injector = get_memory_injector()
        
        # Обновление конфигурации
        if config.memory_budget_ratio is not None:
            injector.memory_budget_ratio = config.memory_budget_ratio
        
        if config.importance_threshold is not None:
            injector.importance_threshold = config.importance_threshold
        
        if config.max_memory_tokens is not None:
            injector.max_memory_tokens = config.max_memory_tokens
        
        if config.memory_type_weights is not None:
            injector.memory_type_weights.update(config.memory_type_weights)
        
        # Очистка кэша после изменения настроек
        injector.relevance_cache.clear()
        injector.token_cache.clear()
        
        return {
            'status': 'success',
            'message': 'Конфигурация обновлена',
            'new_config': {
                'memory_budget_ratio': injector.memory_budget_ratio,
                'importance_threshold': injector.importance_threshold,
                'max_memory_tokens': injector.max_memory_tokens,
                'memory_type_weights': injector.memory_type_weights
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка настройки памяти: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.get('/memory/search_memories')
async def search_memories(
    query: str,
    memory_type: Optional[str] = None,
    limit: int = 10,
    min_importance: float = 0.0
):
    """Поиск воспоминаний в коллективной памяти"""
    try:
        from ..core.collective_mind import get_collective_mind
        
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        # Поиск воспоминаний
        memories = await collective.get_collective_wisdom(query, memory_type, limit)
        
        # Фильтрация по важности
        filtered_memories = [
            memory for memory in memories 
            if memory.importance >= min_importance
        ]
        
        # Сериализация результатов
        result = []
        for memory in filtered_memories:
            result.append({
                'id': memory.id,
                'agent_id': memory.agent_id,
                'type': memory.memory_type,
                'content': memory.content,
                'context': memory.context,
                'importance': memory.importance,
                'verification_count': memory.verification_count,
                'success_rate': memory.success_rate,
                'tags': memory.tags,
                'timestamp': memory.timestamp
            })
        
        return {
            'memories': result,
            'query': query,
            'total_found': len(result),
            'filters': {
                'memory_type': memory_type,
                'min_importance': min_importance,
                'limit': limit
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка поиска воспоминаний: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.post('/memory/optimize_selection')
async def optimize_memory_selection(data: MemoryOptimizeModel):
    """Оптимизация выбора воспоминаний для инъекции"""
    try:
        injector = get_memory_injector()
        
        # Оптимизация выбора
        optimized_memories = await injector.optimize_memory_selection(
            data.prompt, data.available_memories, data.token_budget
        )
        
        # Статистика оптимизации
        total_tokens = sum(mem.get('tokens', 0) for mem in optimized_memories)
        total_importance = sum(mem.get('importance', 0) for mem in optimized_memories)
        
        return {
            'optimized_memories': optimized_memories,
            'optimization_stats': {
                'selected_count': len(optimized_memories),
                'total_available': len(data.available_memories),
                'total_tokens_used': total_tokens,
                'token_budget': data.token_budget,
                'budget_utilization': total_tokens / data.token_budget if data.token_budget > 0 else 0,
                'total_importance': total_importance,
                'avg_importance': total_importance / len(optimized_memories) if optimized_memories else 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка оптимизации: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 