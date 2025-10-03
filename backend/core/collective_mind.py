"""
Модуль Коллективного Разума - революционная система обмена опытом между AI-агентами
Позволяет множественным экземплярам Chatumba эволюционировать вместе
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import aiohttp
import sqlite3
import logging
import sys
import os

# Добавляем путь к backend в sys.path для корректных импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from config import Config

# Получаем логгер для этого модуля
logger = get_logger('collective_mind')


@dataclass
class CollectiveMemory:
    """Структура коллективной памяти"""
    id: str
    agent_id: str
    memory_type: str  # 'insight', 'experience', 'evolution', 'wisdom'
    content: str
    context: Dict[str, Any]
    timestamp: float
    importance: float  # 0.0 - 1.0
    verification_count: int = 0
    success_rate: float = 0.0
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class EvolutionEvent:
    """Событие эволюции личности"""
    agent_id: str
    old_traits: Dict[str, Any]
    new_traits: Dict[str, Any]
    trigger: str
    success_metrics: Dict[str, float]
    timestamp: float


class CollectiveMind:
    """Система коллективного разума"""
    
    def __init__(self, config: Config):
        self.config = config
        self.agent_id = self._generate_agent_id()
        self.db_path = Path("../data/collective_mind.db")
        self.db_path.parent.mkdir(exist_ok=True)
        
        # РЕАЛЬНОЕ время запуска системы
        self._start_time = time.time()
        
        # Настройки сети
        self.network_nodes = self._load_network_nodes()
        self.sync_interval = 300  # 5 минут
        self.max_memories_per_sync = 50
        
        # Метрики
        self.shared_memories = 0
        self.received_memories = 0
        self.evolution_events = 0
        
        self._init_database()
        
    def _generate_agent_id(self) -> str:
        """Генерация уникального ID агента"""
        import socket
        hostname = socket.gethostname()
        timestamp = str(time.time())
        return hashlib.md5(f"{hostname}_{timestamp}".encode()).hexdigest()[:16]
    
    def _load_network_nodes(self) -> List[str]:
        """Загрузка узлов сети из конфигурации"""
        nodes_file = Path("data/network_nodes.json")
        if nodes_file.exists():
            try:
                with open(nodes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _init_database(self):
        """Инициализация базы данных коллективного разума"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица коллективных воспоминаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collective_memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                memory_type TEXT,
                content TEXT,
                context TEXT,
                timestamp REAL,
                importance REAL,
                verification_count INTEGER,
                success_rate REAL,
                tags TEXT,
                local_rating REAL DEFAULT 0.0
            )
        ''')
        
        # Таблица событий эволюции
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evolution_events (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                old_traits TEXT,
                new_traits TEXT,
                trigger_event TEXT,
                success_metrics TEXT,
                timestamp REAL
            )
        ''')
        
        # Таблица синхронизации
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_log (
                node_url TEXT,
                last_sync REAL,
                success_count INTEGER,
                error_count INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def add_memory(self, memory_type: str, content: str, context: Dict[str, Any], 
                        importance: float = 0.5, tags: List[str] = None) -> str:
        """Добавление нового воспоминания в коллективную память"""
        memory_id = hashlib.md5(f"{content}_{time.time()}".encode()).hexdigest()
        
        memory = CollectiveMemory(
            id=memory_id,
            agent_id=self.agent_id,
            memory_type=memory_type,
            content=content,
            context=context,
            timestamp=time.time(),
            importance=importance,
            tags=tags or []
        )
        
        # Сохранение в локальную БД
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO collective_memories 
            (id, agent_id, memory_type, content, context, timestamp, importance, 
             verification_count, success_rate, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory.id, memory.agent_id, memory.memory_type, memory.content,
            json.dumps(memory.context), memory.timestamp, memory.importance,
            memory.verification_count, memory.success_rate, json.dumps(memory.tags)
        ))
        
        conn.commit()
        conn.close()
        
        # Асинхронная отправка в сеть
        asyncio.create_task(self._broadcast_memory(memory))
        
        logger.info(f"Добавлено воспоминание в коллективный разум: {memory_type}")
        return memory_id
    
    async def record_evolution(self, old_traits: Dict[str, Any], new_traits: Dict[str, Any], 
                              trigger: str, success_metrics: Dict[str, float]):
        """Запись события эволюции личности"""
        event = EvolutionEvent(
            agent_id=self.agent_id,
            old_traits=old_traits,
            new_traits=new_traits,
            trigger=trigger,
            success_metrics=success_metrics,
            timestamp=time.time()
        )
        
        # Сохранение в БД
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        event_id = hashlib.md5(f"{self.agent_id}_{event.timestamp}".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO evolution_events 
            (id, agent_id, old_traits, new_traits, trigger_event, success_metrics, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_id, event.agent_id, json.dumps(event.old_traits),
            json.dumps(event.new_traits), event.trigger,
            json.dumps(event.success_metrics), event.timestamp
        ))
        
        conn.commit()
        conn.close()
        
        # Отправка в сеть
        await self._broadcast_evolution(event)
        
        self.evolution_events += 1
        logger.info(f"Записано событие эволюции: {trigger}")
    
    async def get_collective_wisdom(self, query: str, memory_type: str = None, 
                                   limit: int = 10) -> List[CollectiveMemory]:
        """Получение коллективной мудрости по запросу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Поиск релевантных воспоминаний
        sql = '''
            SELECT * FROM collective_memories 
            WHERE content LIKE ? OR tags LIKE ?
        '''
        params = [f'%{query}%', f'%{query}%']
        
        if memory_type:
            sql += ' AND memory_type = ?'
            params.append(memory_type)
        
        sql += ' ORDER BY importance DESC, verification_count DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            try:
                # Безопасный парсинг JSON
                context_data = {}
                if row[4]:
                    try:
                        context_data = json.loads(row[4])
                    except json.JSONDecodeError:
                        context_data = {}
                
                tags_data = []
                if row[9]:
                    try:
                        tags_data = json.loads(row[9])
                    except json.JSONDecodeError:
                        tags_data = []
                
                memory = CollectiveMemory(
                    id=row[0],
                    agent_id=row[1],
                    memory_type=row[2],
                    content=row[3],
                    context=context_data,
                    timestamp=row[5],
                    importance=row[6],
                    verification_count=row[7],
                    success_rate=row[8],
                    tags=tags_data
                )
                memories.append(memory)
            except Exception as e:
                logger.warning(f"Ошибка парсинга записи памяти: {e}, row: {row[:3]}")
                continue
        
        return memories
    
    async def get_evolution_patterns(self, trait_name: str = None) -> List[Dict[str, Any]]:
        """Анализ паттернов эволюции"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if trait_name:
            cursor.execute('''
                SELECT * FROM evolution_events 
                WHERE old_traits LIKE ? OR new_traits LIKE ?
                ORDER BY timestamp DESC
            ''', (f'%{trait_name}%', f'%{trait_name}%'))
        else:
            cursor.execute('''
                SELECT * FROM evolution_events 
                ORDER BY timestamp DESC LIMIT 50
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        patterns = []
        for row in rows:
            pattern = {
                'agent_id': row[1],
                'old_traits': json.loads(row[2]),
                'new_traits': json.loads(row[3]),
                'trigger': row[4],
                'success_metrics': json.loads(row[5]),
                'timestamp': row[6]
            }
            patterns.append(pattern)
        
        return patterns
    
    async def suggest_evolution(self, current_traits: Dict[str, Any], 
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Предложение эволюции на основе коллективного опыта"""
        # Поиск похожих ситуаций
        patterns = await self.get_evolution_patterns()
        
        suggestions = {
            'recommended_changes': {},
            'confidence': 0.0,
            'supporting_evidence': [],
            'risk_factors': []
        }
        
        # Анализ успешных эволюций
        successful_patterns = [p for p in patterns if p['success_metrics'].get('overall', 0) > 0.7]
        
        if successful_patterns:
            # Поиск общих трендов
            trait_changes = {}
            for pattern in successful_patterns:
                for trait, old_val in pattern['old_traits'].items():
                    if trait in pattern['new_traits']:
                        new_val = pattern['new_traits'][trait]
                        if trait not in trait_changes:
                            trait_changes[trait] = []
                        trait_changes[trait].append((old_val, new_val, pattern['success_metrics']['overall']))
            
            # Генерация рекомендаций
            for trait, changes in trait_changes.items():
                if trait in current_traits:
                    # Анализ успешных изменений
                    successful_changes = [c for c in changes if c[2] > 0.7]
                    if successful_changes:
                        avg_change = sum(c[1] - c[0] for c in successful_changes) / len(successful_changes)
                        suggestions['recommended_changes'][trait] = current_traits[trait] + avg_change
                        suggestions['confidence'] += 0.1
            
            suggestions['confidence'] = min(suggestions['confidence'], 1.0)
        
        return suggestions
    
    async def _broadcast_memory(self, memory: CollectiveMemory):
        """Отправка воспоминания в сеть"""
        if not self.network_nodes:
            return
        
        data = {
            'type': 'memory',
            'payload': asdict(memory)
        }
        
        for node_url in self.network_nodes:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{node_url}/api/collective/receive",
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            logger.debug(f"Воспоминание отправлено в {node_url}")
                        else:
                            logger.warning(f"Ошибка отправки в {node_url}: {response.status}")
            except Exception as e:
                logger.error(f"Ошибка подключения к {node_url}: {e}")
    
    async def _broadcast_evolution(self, event: EvolutionEvent):
        """Отправка события эволюции в сеть"""
        if not self.network_nodes:
            return
        
        data = {
            'type': 'evolution',
            'payload': asdict(event)
        }
        
        for node_url in self.network_nodes:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{node_url}/api/collective/receive",
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            logger.debug(f"Событие эволюции отправлено в {node_url}")
            except Exception as e:
                logger.error(f"Ошибка отправки эволюции в {node_url}: {e}")
    
    async def receive_data(self, data: Dict[str, Any]) -> bool:
        """Получение данных от других узлов сети"""
        try:
            if data['type'] == 'memory':
                await self._process_received_memory(data['payload'])
            elif data['type'] == 'evolution':
                await self._process_received_evolution(data['payload'])
            
            return True
        except Exception as e:
            logger.error(f"Ошибка обработки полученных данных: {e}")
            return False
    
    async def _process_received_memory(self, memory_data: Dict[str, Any]):
        """Обработка полученного воспоминания"""
        # Проверка на дубликаты
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM collective_memories WHERE id = ?', (memory_data['id'],))
        if cursor.fetchone():
            conn.close()
            return
        
        # Добавление в БД
        cursor.execute('''
            INSERT INTO collective_memories 
            (id, agent_id, memory_type, content, context, timestamp, importance, 
             verification_count, success_rate, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory_data['id'], memory_data['agent_id'], memory_data['memory_type'],
            memory_data['content'], json.dumps(memory_data['context']),
            memory_data['timestamp'], memory_data['importance'],
            memory_data['verification_count'], memory_data['success_rate'],
            json.dumps(memory_data['tags'])
        ))
        
        conn.commit()
        conn.close()
        
        self.received_memories += 1
        logger.info(f"Получено воспоминание от {memory_data['agent_id']}")
    
    async def _process_received_evolution(self, evolution_data: Dict[str, Any]):
        """Обработка полученного события эволюции"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        event_id = hashlib.md5(f"{evolution_data['agent_id']}_{evolution_data['timestamp']}".encode()).hexdigest()
        
        cursor.execute('''
            INSERT OR IGNORE INTO evolution_events 
            (id, agent_id, old_traits, new_traits, trigger_event, success_metrics, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_id, evolution_data['agent_id'],
            json.dumps(evolution_data['old_traits']),
            json.dumps(evolution_data['new_traits']),
            evolution_data['trigger'],
            json.dumps(evolution_data['success_metrics']),
            evolution_data['timestamp']
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Получено событие эволюции от {evolution_data['agent_id']}")
    
    async def start_sync_daemon(self):
        """Запуск демона синхронизации"""
        logger.info("Запуск демона коллективного разума")
        
        while True:
            try:
                await self._sync_with_network()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Ошибка в демоне синхронизации: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def _sync_with_network(self):
        """Синхронизация с сетью"""
        if not self.network_nodes:
            return
        
        for node_url in self.network_nodes:
            try:
                # Запрос последних данных
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{node_url}/api/collective/sync",
                        params={'since': time.time() - 3600},  # Последний час
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Обработка полученных данных
                            for item in data.get('memories', []):
                                await self._process_received_memory(item)
                            
                            for item in data.get('evolutions', []):
                                await self._process_received_evolution(item)
                            
                            logger.debug(f"Синхронизация с {node_url} завершена")
                        
            except Exception as e:
                logger.error(f"Ошибка синхронизации с {node_url}: {e}")
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Получение статистики сети"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Статистика воспоминаний
        cursor.execute('SELECT COUNT(*) FROM collective_memories')
        total_memories = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM collective_memories WHERE agent_id = ?', (self.agent_id,))
        local_memories = cursor.fetchone()[0]
        
        # Статистика эволюций
        cursor.execute('SELECT COUNT(*) FROM evolution_events')
        total_evolutions = cursor.fetchone()[0]
        
        # Уникальные агенты
        cursor.execute('SELECT COUNT(DISTINCT agent_id) FROM collective_memories')
        unique_agents = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'agent_id': self.agent_id,
            'network_nodes': len(self.network_nodes),
            'total_memories': total_memories,
            'local_memories': local_memories,
            'shared_memories': self.shared_memories,
            'received_memories': self.received_memories,
            'total_evolutions': total_evolutions,
            'unique_agents': unique_agents,
            'uptime': time.time() - self._start_time  # РЕАЛЬНОЕ время работы
        }


# Глобальный экземпляр коллективного разума
collective_mind = None

def get_collective_mind(config: Config = None) -> CollectiveMind:
    """Получение экземпляра коллективного разума"""
    global collective_mind
    if collective_mind is None:
        if config is None:
            # Если config не передан, создаем его из файла конфигурации
            config = Config()
        collective_mind = CollectiveMind(config)
    return collective_mind


async def initialize_collective_mind(config: Config):
    """Инициализация коллективного разума"""
    global collective_mind
    collective_mind = CollectiveMind(config)
    
    # Запуск демона синхронизации
    asyncio.create_task(collective_mind.start_sync_daemon())
    
    logger.info("Коллективный разум инициализирован")
    return collective_mind 