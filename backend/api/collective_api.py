"""
API для коллективного разума - обмен данными между узлами сети
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
from datetime import datetime
from backend.core.collective_mind import get_collective_mind
from backend.utils.logger import get_logger
from backend.config import Config

# Получаем логгер для этого модуля
logger = get_logger('collective_api')

collective_router = APIRouter(tags=["Collective Mind"])

# Модели данных для API
class CollectiveDataModel(BaseModel):
    type: str
    payload: Dict[str, Any]
    timestamp: Optional[float] = None

class EvolutionSuggestionModel(BaseModel):
    current_traits: Dict[str, float]
    context: Dict[str, Any] = {}

class MemoryModel(BaseModel):
    agent_id: str
    memory_type: str
    content: str
    context: Dict[str, Any] = {}
    importance: float = 0.5
    tags: List[str] = []

class EvolutionEventModel(BaseModel):
    agent_id: str
    old_traits: Dict[str, float]
    new_traits: Dict[str, float]
    trigger_event: str
    success_metrics: Dict[str, Any] = {}

class NetworkJoinModel(BaseModel):
    node_url: str
    node_id: Optional[str] = None


@collective_router.post('/collective/receive')
async def receive_collective_data(data: CollectiveDataModel):
    """Получение данных от других узлов сети"""
    try:
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        # Асинхронная обработка данных
        success = await collective.receive_data(data.model_dump())
        
        if success:
            return {'status': 'success', 'message': 'Данные получены'}
        else:
            raise HTTPException(status_code=500, detail='Ошибка обработки данных')
            
    except Exception as e:
        logger.error(f"Ошибка получения коллективных данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@collective_router.get('/collective/sync')
async def sync_collective_data(since: Optional[float] = 0):
    """Синхронизация данных с другими узлами"""
    try:
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        # Получение данных для синхронизации
        import sqlite3
        conn = sqlite3.connect(collective.db_path)
        cursor = conn.cursor()
        
        # Воспоминания
        cursor.execute('''
            SELECT id, agent_id, memory_type, content, context, timestamp, 
                   importance, verification_count, success_rate, tags
            FROM collective_memories 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 100
        ''', (since,))
        
        memory_rows = cursor.fetchall()
        memories = []
        for row in memory_rows:
            memories.append({
                'id': row[0],
                'agent_id': row[1],
                'memory_type': row[2],
                'content': row[3],
                'context': json.loads(row[4]),
                'timestamp': row[5],
                'importance': row[6],
                'verification_count': row[7],
                'success_rate': row[8],
                'tags': json.loads(row[9])
            })
        
        # События эволюции
        cursor.execute('''
            SELECT agent_id, old_traits, new_traits, trigger_event, success_metrics, timestamp
            FROM evolution_events 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 50
        ''', (since,))
        
        evolution_rows = cursor.fetchall()
        evolutions = []
        for row in evolution_rows:
            evolutions.append({
                'agent_id': row[0],
                'old_traits': json.loads(row[1]),
                'new_traits': json.loads(row[2]),
                'trigger': row[3],
                'success_metrics': json.loads(row[4]),
                'timestamp': row[5]
            })
        
        conn.close()
        
        return {
            'memories': memories,
            'evolutions': evolutions,
            'sync_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@collective_router.get('/collective/wisdom')
async def get_collective_wisdom(
    query: str,
    type: Optional[str] = None,
    limit: int = 10
):
    """Получение коллективной мудрости"""
    try:
        if not query:
            raise HTTPException(status_code=400, detail='Необходим параметр query')
        
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        # Асинхронный поиск мудрости
        memories = await collective.get_collective_wisdom(query, type, limit)
        
        # Сериализация результатов
        result = []
        for memory in memories:
            result.append({
                'id': memory.id,
                'agent_id': memory.agent_id,
                'type': memory.memory_type,
                'content': memory.content,
                'context': memory.context,
                'timestamp': memory.timestamp,
                'importance': memory.importance,
                'verification_count': memory.verification_count,
                'success_rate': memory.success_rate,
                'tags': memory.tags
            })
        
        return {
            'wisdom': result,
            'query': query,
            'total_found': len(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения мудрости: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@collective_router.post('/collective/evolution/suggest')
async def suggest_evolution(data: EvolutionSuggestionModel):
    """Предложение эволюции на основе коллективного опыта"""
    try:
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        # Получение предложений
        suggestions = await collective.suggest_evolution(data.current_traits, data.context)
        
        return {
            'suggestions': suggestions,
            'current_traits': data.current_traits,
            'context': data.context,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка предложения эволюции: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@collective_router.get('/collective/evolution/patterns')
async def get_evolution_patterns():
    """Получение паттернов эволюции"""
    try:
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        # Получение паттернов из базы данных
        import sqlite3
        conn = sqlite3.connect(collective.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT trigger_event, COUNT(*) as frequency,
                   AVG(json_extract(success_metrics, '$.success_rate')) as avg_success
            FROM evolution_events
            GROUP BY trigger_event
            ORDER BY frequency DESC
            LIMIT 20
        ''')
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                'trigger': row[0],
                'frequency': row[1],
                'avg_success_rate': row[2] or 0
            })
        
        conn.close()
        
        return {
            'patterns': patterns,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения паттернов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@collective_router.get('/collective/stats')
async def get_network_stats():
    """Получение статистики сети"""
    try:
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        stats = await collective.get_network_stats()
        
        return {
            'network_stats': stats,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@collective_router.post('/collective/add_memory')
async def add_collective_memory(memory: MemoryModel):
    """Добавление воспоминания в коллективную память"""
    try:
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        # Создание объекта воспоминания
        from ..core.collective_mind import CollectiveMemory
        collective_memory = CollectiveMemory(
            id=f"manual_{datetime.now().timestamp()}",
            agent_id=memory.agent_id,
            memory_type=memory.memory_type,
            content=memory.content,
            context=memory.context,
            timestamp=datetime.now().timestamp(),
            importance=memory.importance,
            verification_count=1,
            success_rate=1.0,
            tags=memory.tags
        )
        
        # Добавление в коллективную память
        success = await collective.add_memory(collective_memory)
        
        if success:
            return {
                'status': 'success',
                'message': 'Воспоминание добавлено',
                'memory_id': collective_memory.id
            }
        else:
            raise HTTPException(status_code=500, detail='Ошибка добавления воспоминания')
            
    except Exception as e:
        logger.error(f"Ошибка добавления воспоминания: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@collective_router.post('/collective/record_evolution')
async def record_evolution_event(event: EvolutionEventModel):
    """Запись события эволюции"""
    try:
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        # Создание объекта события
        from ..core.collective_mind import EvolutionEvent
        evolution_event = EvolutionEvent(
            agent_id=event.agent_id,
            old_traits=event.old_traits,
            new_traits=event.new_traits,
            trigger_event=event.trigger_event,
            success_metrics=event.success_metrics,
            timestamp=datetime.now().timestamp()
        )
        
        # Запись события
        success = await collective.record_evolution(evolution_event)
        
        if success:
            return {
                'status': 'success',
                'message': 'Событие эволюции записано',
                'event_id': f"{event.agent_id}_{evolution_event.timestamp}"
            }
        else:
            raise HTTPException(status_code=500, detail='Ошибка записи события')
            
    except Exception as e:
        logger.error(f"Ошибка записи эволюции: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@collective_router.post('/collective/network/join')
async def join_network(data: NetworkJoinModel):
    """Присоединение к сети коллективного разума"""
    try:
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        # Добавление узла в сеть
        success = await collective.add_network_node(data.node_url, data.node_id)
        
        if success:
            return {
                'status': 'success',
                'message': f'Узел {data.node_url} добавлен в сеть',
                'node_url': data.node_url,
                'node_id': data.node_id
            }
        else:
            raise HTTPException(status_code=500, detail='Ошибка добавления узла')
            
    except Exception as e:
        logger.error(f"Ошибка присоединения к сети: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@collective_router.get('/collective/network/nodes')
async def get_network_nodes():
    """Получение списка узлов сети"""
    try:
        collective = get_collective_mind()
        if not collective:
            raise HTTPException(status_code=503, detail='Коллективный разум не инициализирован')
        
        nodes = await collective.get_network_nodes()
        
        return {
            'nodes': nodes,
            'total_nodes': len(nodes),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения узлов сети: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 