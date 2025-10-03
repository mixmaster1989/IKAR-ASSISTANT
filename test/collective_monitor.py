#!/usr/bin/env python3
"""
🔍 Монитор агентов коллективного разума IKAR
Инструмент для мониторинга в реальном времени
"""

import sqlite3
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
import curses
import threading
from collections import defaultdict, Counter

class CollectiveMonitor:
    """Монитор коллективного разума в реальном времени"""
    
    def __init__(self, db_path: str = "data/collective_mind.db"):
        self.db_path = Path(db_path)
        self.running = False
        self.last_check = datetime.now()
        self.agents_cache = {}
        self.network_stats = {}
        
    def get_current_stats(self) -> Dict[str, Any]:
        """Получение текущей статистики"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute("SELECT COUNT(DISTINCT agent_id) FROM collective_memories")
            total_agents = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM collective_memories")
            total_memories = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM evolution_events")
            total_evolution = cursor.fetchone()[0] or 0
            
            # Активность за последний час
            hour_ago = (datetime.now() - timedelta(hours=1)).timestamp()
            cursor.execute("""
                SELECT COUNT(DISTINCT agent_id) 
                FROM collective_memories 
                WHERE timestamp > ?
            """, (hour_ago,))
            active_agents_hour = cursor.fetchone()[0] or 0
            
            # Активность за последние 24 часа
            day_ago = (datetime.now() - timedelta(days=1)).timestamp()
            cursor.execute("""
                SELECT COUNT(DISTINCT agent_id) 
                FROM collective_memories 
                WHERE timestamp > ?
            """, (day_ago,))
            active_agents_day = cursor.fetchone()[0] or 0
            
            # Новые агенты за последние 24 часа
            cursor.execute("""
                SELECT COUNT(DISTINCT agent_id) 
                FROM collective_memories 
                WHERE agent_id NOT IN (
                    SELECT DISTINCT agent_id 
                    FROM collective_memories 
                    WHERE timestamp <= ?
                )
            """, (day_ago,))
            new_agents_day = cursor.fetchone()[0] or 0
            
            # Топ агентов по активности
            cursor.execute("""
                SELECT agent_id, COUNT(*) as memory_count
                FROM collective_memories
                WHERE timestamp > ?
                GROUP BY agent_id
                ORDER BY memory_count DESC
                LIMIT 5
            """, (day_ago,))
            top_agents = cursor.fetchall()
            
            # Статистика по типам памяти
            cursor.execute("""
                SELECT memory_type, COUNT(*) 
                FROM collective_memories 
                WHERE timestamp > ?
                GROUP BY memory_type
                ORDER BY COUNT(*) DESC
            """, (day_ago,))
            memory_types = dict(cursor.fetchall())
            
            # Последние события
            cursor.execute("""
                SELECT agent_id, memory_type, timestamp
                FROM collective_memories
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            recent_events = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_agents': total_agents,
                'total_memories': total_memories,
                'total_evolution': total_evolution,
                'active_agents_hour': active_agents_hour,
                'active_agents_day': active_agents_day,
                'new_agents_day': new_agents_day,
                'top_agents': top_agents,
                'memory_types': memory_types,
                'recent_events': recent_events,
                'last_update': datetime.now()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'last_update': datetime.now()
            }
    
    def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Получение детальной информации об агенте"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Базовая информация
            cursor.execute("""
                SELECT MIN(timestamp), MAX(timestamp), COUNT(*)
                FROM collective_memories
                WHERE agent_id = ?
            """, (agent_id,))
            
            first_seen, last_seen, total_memories = cursor.fetchone()
            
            # Типы памяти
            cursor.execute("""
                SELECT memory_type, COUNT(*)
                FROM collective_memories
                WHERE agent_id = ?
                GROUP BY memory_type
            """, (agent_id,))
            
            memory_types = dict(cursor.fetchall())
            
            # Эволюционные события
            cursor.execute("""
                SELECT COUNT(*)
                FROM evolution_events
                WHERE agent_id = ?
            """, (agent_id,))
            
            evolution_count = cursor.fetchone()[0] or 0
            
            # Последние воспоминания
            cursor.execute("""
                SELECT memory_type, content, importance, timestamp
                FROM collective_memories
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT 5
            """, (agent_id,))
            
            recent_memories = cursor.fetchall()
            
            conn.close()
            
            return {
                'agent_id': agent_id,
                'first_seen': datetime.fromtimestamp(first_seen) if first_seen else None,
                'last_seen': datetime.fromtimestamp(last_seen) if last_seen else None,
                'total_memories': total_memories,
                'memory_types': memory_types,
                'evolution_count': evolution_count,
                'recent_memories': recent_memories
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def run_terminal_monitor(self):
        """Запуск терминального монитора"""
        def monitor_loop():
            while self.running:
                try:
                    stats = self.get_current_stats()
                    self.display_stats(stats)
                    time.sleep(5)  # Обновление каждые 5 секунд
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Ошибка мониторинга: {e}")
                    time.sleep(10)
        
        self.running = True
        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.start()
        
        try:
            monitor_thread.join()
        except KeyboardInterrupt:
            self.running = False
            print("\n🛑 Мониторинг остановлен")
    
    def display_stats(self, stats: Dict[str, Any]):
        """Отображение статистики в терминале"""
        # Очистка экрана
        print("\033[2J\033[H")
        
        print("🧬 **МОНИТОР КОЛЛЕКТИВНОГО РАЗУМА IKAR**")
        print("=" * 60)
        print(f"📅 Последнее обновление: {stats['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if 'error' in stats:
            print(f"❌ Ошибка: {stats['error']}")
            return
        
        # Общая статистика
        print("📊 **ОБЩАЯ СТАТИСТИКА**")
        print("-" * 30)
        print(f"🤖 Всего агентов: {stats['total_agents']}")
        print(f"🧠 Общих воспоминаний: {stats['total_memories']}")
        print(f"🔄 Событий эволюции: {stats['total_evolution']}")
        print()
        
        # Активность
        print("⚡ **АКТИВНОСТЬ**")
        print("-" * 30)
        print(f"🕐 За последний час: {stats['active_agents_hour']} агентов")
        print(f"📅 За последние 24 часа: {stats['active_agents_day']} агентов")
        print(f"🆕 Новых агентов за день: {stats['new_agents_day']}")
        print()
        
        # Топ агентов
        print("🏆 **ТОП-5 АГЕНТОВ ПО АКТИВНОСТИ (24ч)**")
        print("-" * 30)
        for i, (agent_id, count) in enumerate(stats['top_agents'], 1):
            print(f"{i}. {agent_id[:16]}... - {count} воспоминаний")
        print()
        
        # Типы памяти
        print("🧠 **ТИПЫ ПАМЯТИ (24ч)**")
        print("-" * 30)
        for mem_type, count in stats['memory_types'].items():
            print(f"• {mem_type}: {count}")
        print()
        
        # Последние события
        print("🕐 **ПОСЛЕДНИЕ СОБЫТИЯ**")
        print("-" * 30)
        for agent_id, mem_type, timestamp in stats['recent_events']:
            time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            print(f"• {time_str} - {agent_id[:16]}... ({mem_type})")
        print()
        
        print("=" * 60)
        print("Нажмите Ctrl+C для остановки")
    
    async def generate_live_report(self) -> str:
        """Генерация живого отчета"""
        stats = self.get_current_stats()
        
        if 'error' in stats:
            return f"❌ Ошибка получения данных: {stats['error']}"
        
        report = []
        report.append("🧬 **ЖИВОЙ ОТЧЕТ КОЛЛЕКТИВНОГО РАЗУМА**")
        report.append("=" * 60)
        report.append(f"📅 Время: {stats['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Общая статистика
        report.append("📊 **ОБЩАЯ СТАТИСТИКА**")
        report.append("-" * 30)
        report.append(f"🤖 Всего агентов: {stats['total_agents']}")
        report.append(f"🧠 Общих воспоминаний: {stats['total_memories']}")
        report.append(f"🔄 Событий эволюции: {stats['total_evolution']}")
        report.append("")
        
        # Активность
        report.append("⚡ **АКТИВНОСТЬ ЗА ПОСЛЕДНИЕ 24 ЧАСА**")
        report.append("-" * 30)
        report.append(f"🕐 Активных агентов: {stats['active_agents_day']}")
        report.append(f"🆕 Новых агентов: {stats['new_agents_day']}")
        report.append("")
        
        # Топ агентов
        report.append("🏆 **ТОП-5 АГЕНТОВ ПО АКТИВНОСТИ**")
        report.append("-" * 30)
        for i, (agent_id, count) in enumerate(stats['top_agents'], 1):
            report.append(f"{i}. **{agent_id[:16]}...** - {count} воспоминаний")
        report.append("")
        
        # Типы памяти
        report.append("🧠 **РАСПРЕДЕЛЕНИЕ ПО ТИПАМ ПАМЯТИ**")
        report.append("-" * 30)
        total_memories_24h = sum(stats['memory_types'].values())
        for mem_type, count in stats['memory_types'].items():
            percentage = (count / total_memories_24h * 100) if total_memories_24h > 0 else 0
            report.append(f"• {mem_type.upper()}: {count} ({percentage:.1f}%)")
        report.append("")
        
        # Последние события
        report.append("🕐 **ПОСЛЕДНИЕ 10 СОБЫТИЙ**")
        report.append("-" * 30)
        for agent_id, mem_type, timestamp in stats['recent_events']:
            time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            report.append(f"• {time_str} - {agent_id[:16]}... ({mem_type})")
        report.append("")
        
        # Анализ трендов
        report.append("📈 **АНАЛИЗ ТРЕНДОВ**")
        report.append("-" * 30)
        
        if stats['new_agents_day'] > 0:
            report.append("🟢 Рост сети - новые агенты присоединяются")
        else:
            report.append("🟡 Стабильная сеть - нет новых агентов")
        
        if stats['active_agents_day'] > stats['total_agents'] * 0.5:
            report.append("🟢 Высокая активность - большинство агентов активны")
        elif stats['active_agents_day'] > stats['total_agents'] * 0.2:
            report.append("🟡 Умеренная активность")
        else:
            report.append("🔴 Низкая активность - большинство агентов неактивны")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)

async def main():
    """Основная функция"""
    print("🔍 Запуск монитора коллективного разума IKAR")
    print("=" * 60)
    
    monitor = CollectiveMonitor()
    
    # Проверяем существование базы данных
    if not monitor.db_path.exists():
        print(f"❌ База данных не найдена: {monitor.db_path}")
        print("Убедитесь, что система коллективного разума запущена")
        return
    
    print("📊 Генерация живого отчета...")
    report = await monitor.generate_live_report()
    
    # Сохраняем отчет
    report_file = Path("reports/live_collective_report.txt")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("📊 Отчет сохранен в reports/live_collective_report.txt")
    print("\n" + "=" * 60)
    print(report)
    
    # Запуск терминального монитора
    print("\n🔍 Запуск терминального монитора...")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        monitor.run_terminal_monitor()
    except KeyboardInterrupt:
        print("\n🛑 Мониторинг остановлен")

if __name__ == "__main__":
    asyncio.run(main()) 