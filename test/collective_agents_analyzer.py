#!/usr/bin/env python3
"""
🧬 Анализатор агентов коллективного разума IKAR
Инструмент для мониторинга и анализа уникальных агентов в системе
"""

import sqlite3
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
import aiohttp
from dataclasses import dataclass
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter

@dataclass
class AgentInfo:
    """Информация об агенте"""
    agent_id: str
    first_seen: datetime
    last_seen: datetime
    total_memories: int
    memory_types: Dict[str, int]
    evolution_events: int
    network_nodes: List[str]
    success_rate: float
    activity_level: str
    personality_traits: Dict[str, Any]
    collective_contributions: int
    wisdom_score: float
    network_influence: float

class CollectiveAgentsAnalyzer:
    """Анализатор агентов коллективного разума"""
    
    def __init__(self, db_path: str = "data/collective_mind.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.agents_data = {}
        self.network_stats = {}
        
    def _init_database(self):
        """Инициализация базы данных для анализа"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для отслеживания агентов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_tracking (
                agent_id TEXT PRIMARY KEY,
                first_seen REAL,
                last_seen REAL,
                total_memories INTEGER DEFAULT 0,
                evolution_events INTEGER DEFAULT 0,
                network_nodes TEXT,
                success_rate REAL DEFAULT 0.0,
                personality_traits TEXT,
                collective_contributions INTEGER DEFAULT 0,
                wisdom_score REAL DEFAULT 0.0,
                network_influence REAL DEFAULT 0.0,
                activity_level TEXT DEFAULT 'low'
            )
        ''')
        
        # Таблица для детального анализа памяти
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_memory_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                memory_type TEXT,
                content_preview TEXT,
                importance REAL,
                timestamp REAL,
                verification_count INTEGER,
                success_rate REAL,
                tags TEXT,
                FOREIGN KEY (agent_id) REFERENCES agent_tracking (agent_id)
            )
        ''')
        
        # Таблица для анализа эволюции
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_evolution_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                old_traits TEXT,
                new_traits TEXT,
                trigger_event TEXT,
                success_metrics TEXT,
                timestamp REAL,
                validation_score REAL,
                FOREIGN KEY (agent_id) REFERENCES agent_tracking (agent_id)
            )
        ''')
        
        # Таблица для сетевого взаимодействия
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_agent TEXT,
                target_agent TEXT,
                interaction_type TEXT,
                data_size INTEGER,
                timestamp REAL,
                success BOOLEAN,
                FOREIGN KEY (source_agent) REFERENCES agent_tracking (agent_id),
                FOREIGN KEY (target_agent) REFERENCES agent_tracking (agent_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def scan_collective_database(self) -> Dict[str, AgentInfo]:
        """Сканирование базы данных коллективного разума"""
        print("🔍 Сканирование базы данных коллективного разума...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем всех уникальных агентов
        cursor.execute('''
            SELECT DISTINCT agent_id FROM collective_memories
            UNION
            SELECT DISTINCT agent_id FROM evolution_events
        ''')
        
        agent_ids = [row[0] for row in cursor.fetchall()]
        print(f"📊 Найдено {len(agent_ids)} уникальных агентов")
        
        agents_info = {}
        
        for agent_id in agent_ids:
            print(f"🔍 Анализ агента: {agent_id[:16]}...")
            
            # Базовая информация об агенте
            agent_info = await self._analyze_agent(cursor, agent_id)
            agents_info[agent_id] = agent_info
            
            # Сохраняем в таблицу отслеживания
            self._save_agent_tracking(cursor, agent_info)
        
        conn.commit()
        conn.close()
        
        return agents_info
    
    async def _analyze_agent(self, cursor, agent_id: str) -> AgentInfo:
        """Анализ конкретного агента"""
        
        # Анализ воспоминаний
        cursor.execute('''
            SELECT memory_type, content, importance, timestamp, 
                   verification_count, success_rate, tags
            FROM collective_memories 
            WHERE agent_id = ?
            ORDER BY timestamp DESC
        ''', (agent_id,))
        
        memories = cursor.fetchall()
        
        # Анализ эволюции
        cursor.execute('''
            SELECT old_traits, new_traits, trigger_event, 
                   success_metrics, timestamp
            FROM evolution_events 
            WHERE agent_id = ?
            ORDER BY timestamp DESC
        ''', (agent_id,))
        
        evolution_events = cursor.fetchall()
        
        # Статистика по типам памяти
        memory_types = Counter()
        total_importance = 0
        total_verifications = 0
        total_success = 0
        
        for memory in memories:
            memory_type = memory[0]
            memory_types[memory_type] += 1
            total_importance += memory[2] or 0
            total_verifications += memory[4] or 0
            total_success += memory[5] or 0
        
        # Расчет метрик
        avg_importance = total_importance / len(memories) if memories else 0
        avg_verifications = total_verifications / len(memories) if memories else 0
        avg_success = total_success / len(memories) if memories else 0
        
        # Определение уровня активности
        if len(memories) > 100:
            activity_level = "very_high"
        elif len(memories) > 50:
            activity_level = "high"
        elif len(memories) > 20:
            activity_level = "medium"
        elif len(memories) > 5:
            activity_level = "low"
        else:
            activity_level = "inactive"
        
        # Анализ личности (из эволюционных событий)
        personality_traits = {}
        if evolution_events:
            latest_evolution = evolution_events[0]
            try:
                new_traits = json.loads(latest_evolution[1])
                personality_traits = new_traits
            except:
                pass
        
        # Расчет мудрости и влияния
        wisdom_score = (avg_importance * 0.4 + avg_verifications * 0.3 + avg_success * 0.3)
        network_influence = len(memories) * avg_verifications * 0.1
        
        # Временные метки
        timestamps = [m[3] for m in memories] + [e[4] for e in evolution_events]
        if timestamps:
            first_seen = datetime.fromtimestamp(min(timestamps))
            last_seen = datetime.fromtimestamp(max(timestamps))
        else:
            first_seen = last_seen = datetime.now()
        
        return AgentInfo(
            agent_id=agent_id,
            first_seen=first_seen,
            last_seen=last_seen,
            total_memories=len(memories),
            memory_types=dict(memory_types),
            evolution_events=len(evolution_events),
            network_nodes=[],  # Будет заполнено позже
            success_rate=avg_success,
            activity_level=activity_level,
            personality_traits=personality_traits,
            collective_contributions=len(memories),
            wisdom_score=wisdom_score,
            network_influence=network_influence
        )
    
    def _save_agent_tracking(self, cursor, agent_info: AgentInfo):
        """Сохранение информации об агенте в таблицу отслеживания"""
        cursor.execute('''
            INSERT OR REPLACE INTO agent_tracking 
            (agent_id, first_seen, last_seen, total_memories, evolution_events,
             network_nodes, success_rate, personality_traits, 
             collective_contributions, wisdom_score, network_influence, activity_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            agent_info.agent_id,
            agent_info.first_seen.timestamp(),
            agent_info.last_seen.timestamp(),
            agent_info.total_memories,
            agent_info.evolution_events,
            json.dumps(agent_info.network_nodes),
            agent_info.success_rate,
            json.dumps(agent_info.personality_traits),
            agent_info.collective_contributions,
            agent_info.wisdom_score,
            agent_info.network_influence,
            agent_info.activity_level
        ))
    
    async def generate_comprehensive_report(self) -> str:
        """Генерация комплексного отчета по агентам"""
        print("📊 Генерация комплексного отчета...")
        
        # Сканируем базу данных
        agents_info = await self.scan_collective_database()
        
        if not agents_info:
            return "❌ Агенты не найдены в базе данных"
        
        # Создаем отчет
        report = []
        report.append("🧬 **ОТЧЕТ О РЕАЛЬНОМ СОСТОЯНИИ СИСТЕМЫ IKAR**")
        report.append("=" * 60)
        report.append("")
        
        # Общая статистика
        report.append("📈 **ОБЩАЯ СТАТИСТИКА**")
        report.append("-" * 30)
        total_memories = sum(agent.total_memories for agent in agents_info.values())
        total_evolution = sum(agent.evolution_events for agent in agents_info.values())
        avg_wisdom = sum(agent.wisdom_score for agent in agents_info.values()) / len(agents_info)
        
        report.append(f"🤖 **Всего агентов:** {len(agents_info)}")
        report.append(f"🧠 **Общих воспоминаний:** {total_memories}")
        report.append(f"🔄 **Событий эволюции:** {total_evolution}")
        report.append(f"📊 **Средний уровень мудрости:** {avg_wisdom:.2f}")
        report.append("")
        
        # Анализ по активности
        activity_stats = Counter(agent.activity_level for agent in agents_info.values())
        report.append("⚡ **РАСПРЕДЕЛЕНИЕ ПО АКТИВНОСТИ**")
        report.append("-" * 30)
        for level, count in activity_stats.most_common():
            percentage = (count / len(agents_info)) * 100
            report.append(f"• {level.upper()}: {count} агентов ({percentage:.1f}%)")
        report.append("")
        
        # Топ агентов по мудрости
        report.append("🏆 **ТОП-5 АГЕНТОВ ПО МУДРОСТИ**")
        report.append("-" * 30)
        top_wisdom = sorted(agents_info.values(), key=lambda x: x.wisdom_score, reverse=True)[:5]
        for i, agent in enumerate(top_wisdom, 1):
            report.append(f"{i}. **{agent.agent_id[:16]}...**")
            report.append(f"   🧠 Мудрость: {agent.wisdom_score:.2f}")
            report.append(f"   📝 Воспоминаний: {agent.total_memories}")
            report.append(f"   🔄 Эволюций: {agent.evolution_events}")
            report.append(f"   ⚡ Активность: {agent.activity_level}")
            report.append("")
        
        # Топ агентов по влиянию
        report.append("🌟 **ТОП-5 АГЕНТОВ ПО СЕТЕВОМУ ВЛИЯНИЮ**")
        report.append("-" * 30)
        top_influence = sorted(agents_info.values(), key=lambda x: x.network_influence, reverse=True)[:5]
        for i, agent in enumerate(top_influence, 1):
            report.append(f"{i}. **{agent.agent_id[:16]}...**")
            report.append(f"   🌐 Влияние: {agent.network_influence:.2f}")
            report.append(f"   📊 Успешность: {agent.success_rate:.2f}")
            report.append(f"   🏆 Вклад: {agent.collective_contributions}")
            report.append("")
        
        # Анализ типов памяти
        report.append("🧠 **АНАЛИЗ ТИПОВ ПАМЯТИ**")
        report.append("-" * 30)
        all_memory_types = Counter()
        for agent in agents_info.values():
            all_memory_types.update(agent.memory_types)
        
        for memory_type, count in all_memory_types.most_common():
            percentage = (count / total_memories) * 100
            report.append(f"• {memory_type.upper()}: {count} ({percentage:.1f}%)")
        report.append("")
        
        # Детальный анализ каждого агента
        report.append("🔍 **ДЕТАЛЬНЫЙ АНАЛИЗ АГЕНТОВ**")
        report.append("=" * 60)
        
        for agent_id, agent in agents_info.items():
            report.append(f"🤖 **АГЕНТ: {agent_id[:16]}...**")
            report.append(f"📅 Первое появление: {agent.first_seen.strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"📅 Последняя активность: {agent.last_seen.strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"⏱️ Время работы: {agent.last_seen - agent.first_seen}")
            report.append(f"📝 Всего воспоминаний: {agent.total_memories}")
            report.append(f"🔄 Событий эволюции: {agent.evolution_events}")
            report.append(f"🧠 Уровень мудрости: {agent.wisdom_score:.2f}")
            report.append(f"🌟 Сетевое влияние: {agent.network_influence:.2f}")
            report.append(f"📊 Успешность: {agent.success_rate:.2f}")
            report.append(f"⚡ Уровень активности: {agent.activity_level}")
            
            if agent.memory_types:
                report.append("📚 Типы воспоминаний:")
                for mem_type, count in agent.memory_types.items():
                    report.append(f"   • {mem_type}: {count}")
            
            if agent.personality_traits:
                report.append("🎭 Черты личности:")
                for trait, value in agent.personality_traits.items():
                    report.append(f"   • {trait}: {value}")
            
            report.append("-" * 40)
            report.append("")
        
        # Рекомендации
        report.append("💡 **РЕКОМЕНДАЦИИ**")
        report.append("=" * 30)
        
        inactive_agents = [a for a in agents_info.values() if a.activity_level == "inactive"]
        if inactive_agents:
            report.append(f"⚠️ {len(inactive_agents)} неактивных агентов требуют внимания")
        
        low_wisdom_agents = [a for a in agents_info.values() if a.wisdom_score < 0.3]
        if low_wisdom_agents:
            report.append(f"📚 {len(low_wisdom_agents)} агентов с низкой мудростью нуждаются в обучении")
        
        high_influence_agents = [a for a in agents_info.values() if a.network_influence > 10]
        if high_influence_agents:
            report.append(f"🌟 {len(high_influence_agents)} высоковлиятельных агентов - ключевые узлы сети")
        
        report.append("")
        report.append("📊 **Отчет сгенерирован:** " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return "\n".join(report)
    
    async def generate_visual_report(self, output_dir: str = "reports"):
        """Генерация визуального отчета с графиками"""
        print("📊 Генерация визуального отчета...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Получаем данные
        agents_info = await self.scan_collective_database()
        
        if not agents_info:
            print("❌ Нет данных для визуализации")
            return
        
        # Создаем DataFrame
        data = []
        for agent in agents_info.values():
            data.append({
                'agent_id': agent.agent_id[:16],
                'total_memories': agent.total_memories,
                'evolution_events': agent.evolution_events,
                'wisdom_score': agent.wisdom_score,
                'network_influence': agent.network_influence,
                'success_rate': agent.success_rate,
                'activity_level': agent.activity_level,
                'days_active': (agent.last_seen - agent.first_seen).days
            })
        
        df = pd.DataFrame(data)
        
        # Настройка стиля
        plt.style.use('dark_background')
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('🧬 Анализ агентов коллективного разума IKAR', fontsize=16, color='white')
        
        # 1. Распределение по активности
        activity_counts = df['activity_level'].value_counts()
        axes[0, 0].pie(activity_counts.values, labels=activity_counts.index, autopct='%1.1f%%')
        axes[0, 0].set_title('Распределение по активности', color='white')
        
        # 2. Мудрость vs Влияние
        axes[0, 1].scatter(df['wisdom_score'], df['network_influence'], alpha=0.7)
        axes[0, 1].set_xlabel('Уровень мудрости', color='white')
        axes[0, 1].set_ylabel('Сетевое влияние', color='white')
        axes[0, 1].set_title('Мудрость vs Влияние', color='white')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Количество воспоминаний
        axes[0, 2].hist(df['total_memories'], bins=10, alpha=0.7, color='cyan')
        axes[0, 2].set_xlabel('Количество воспоминаний', color='white')
        axes[0, 2].set_ylabel('Количество агентов', color='white')
        axes[0, 2].set_title('Распределение воспоминаний', color='white')
        axes[0, 2].grid(True, alpha=0.3)
        
        # 4. Успешность по активности
        success_by_activity = df.groupby('activity_level')['success_rate'].mean()
        axes[1, 0].bar(success_by_activity.index, success_by_activity.values, color='green')
        axes[1, 0].set_xlabel('Уровень активности', color='white')
        axes[1, 0].set_ylabel('Средняя успешность', color='white')
        axes[1, 0].set_title('Успешность по активности', color='white')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. Эволюция агентов
        axes[1, 1].scatter(df['days_active'], df['evolution_events'], alpha=0.7, color='orange')
        axes[1, 1].set_xlabel('Дни активности', color='white')
        axes[1, 1].set_ylabel('События эволюции', color='white')
        axes[1, 1].set_title('Эволюция по времени', color='white')
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. Топ агентов по мудрости
        top_agents = df.nlargest(10, 'wisdom_score')
        axes[1, 2].barh(top_agents['agent_id'], top_agents['wisdom_score'], color='purple')
        axes[1, 2].set_xlabel('Уровень мудрости', color='white')
        axes[1, 2].set_title('Топ-10 агентов по мудрости', color='white')
        axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path / 'collective_agents_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Визуальный отчет сохранен: {output_path / 'collective_agents_analysis.png'}")
    
    async def export_agent_data(self, output_dir: str = "reports") -> str:
        """Экспорт данных агентов в JSON и CSV"""
        print("📤 Экспорт данных агентов...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        agents_info = await self.scan_collective_database()
        
        # Экспорт в JSON
        json_data = {}
        for agent_id, agent in agents_info.items():
            json_data[agent_id] = {
                'agent_id': agent.agent_id,
                'first_seen': agent.first_seen.isoformat(),
                'last_seen': agent.last_seen.isoformat(),
                'total_memories': agent.total_memories,
                'memory_types': agent.memory_types,
                'evolution_events': agent.evolution_events,
                'network_nodes': agent.network_nodes,
                'success_rate': agent.success_rate,
                'activity_level': agent.activity_level,
                'personality_traits': agent.personality_traits,
                'collective_contributions': agent.collective_contributions,
                'wisdom_score': agent.wisdom_score,
                'network_influence': agent.network_influence
            }
        
        json_file = output_path / 'agents_data.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Экспорт в CSV
        csv_data = []
        for agent in agents_info.values():
            csv_data.append({
                'agent_id': agent.agent_id,
                'first_seen': agent.first_seen,
                'last_seen': agent.last_seen,
                'total_memories': agent.total_memories,
                'evolution_events': agent.evolution_events,
                'success_rate': agent.success_rate,
                'activity_level': agent.activity_level,
                'wisdom_score': agent.wisdom_score,
                'network_influence': agent.network_influence,
                'collective_contributions': agent.collective_contributions
            })
        
        df = pd.DataFrame(csv_data)
        csv_file = output_path / 'agents_data.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"📤 Данные экспортированы:")
        print(f"   JSON: {json_file}")
        print(f"   CSV: {csv_file}")
        
        return f"Экспорт завершен: {json_file}, {csv_file}"

async def main():
    """Основная функция"""
    print("🧬 Запуск анализатора агентов коллективного разума IKAR")
    print("=" * 60)
    
    analyzer = CollectiveAgentsAnalyzer()
    analyzer._init_database()
    
    # Генерируем отчет
    report = await analyzer.generate_comprehensive_report()
    
    # Сохраняем отчет
    report_file = Path("reports/collective_agents_report.txt")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("📊 Отчет сохранен в reports/collective_agents_report.txt")
    print("\n" + "=" * 60)
    print(report)
    
    # Генерируем визуальный отчет
    await analyzer.generate_visual_report()
    
    # Экспортируем данные
    await analyzer.export_agent_data()
    
    print("\n✅ Анализ завершен!")

if __name__ == "__main__":
    asyncio.run(main()) 