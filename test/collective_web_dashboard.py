#!/usr/bin/env python3
"""
🌐 Веб-дашборд для мониторинга агентов коллективного разума IKAR
"""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel

app = FastAPI(title="IKAR Collective Mind Dashboard", version="1.0.0")

class CollectiveAnalyzer:
    """Анализатор коллективного разума для веб-интерфейса"""
    
    def __init__(self, db_path: str = "data/collective_mind.db"):
        self.db_path = Path(db_path)
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """Получение общей статистики"""
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
            
            # Активность за последние периоды
            hour_ago = (datetime.now() - timedelta(hours=1)).timestamp()
            day_ago = (datetime.now() - timedelta(days=1)).timestamp()
            week_ago = (datetime.now() - timedelta(days=7)).timestamp()
            
            cursor.execute("SELECT COUNT(DISTINCT agent_id) FROM collective_memories WHERE timestamp > ?", (hour_ago,))
            active_hour = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(DISTINCT agent_id) FROM collective_memories WHERE timestamp > ?", (day_ago,))
            active_day = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(DISTINCT agent_id) FROM collective_memories WHERE timestamp > ?", (week_ago,))
            active_week = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_agents': total_agents,
                'total_memories': total_memories,
                'total_evolution': total_evolution,
                'active_hour': active_hour,
                'active_day': active_day,
                'active_week': active_week,
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_agents_list(self) -> List[Dict[str, Any]]:
        """Получение списка всех агентов"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT agent_id, 
                       MIN(timestamp) as first_seen,
                       MAX(timestamp) as last_seen,
                       COUNT(*) as memory_count
                FROM collective_memories
                GROUP BY agent_id
                ORDER BY memory_count DESC
            """)
            
            agents = []
            for row in cursor.fetchall():
                agent_id, first_seen, last_seen, memory_count = row
                
                # Получаем типы памяти
                cursor.execute("""
                    SELECT memory_type, COUNT(*)
                    FROM collective_memories
                    WHERE agent_id = ?
                    GROUP BY memory_type
                """, (agent_id,))
                
                memory_types = dict(cursor.fetchall())
                
                # Получаем эволюционные события
                cursor.execute("SELECT COUNT(*) FROM evolution_events WHERE agent_id = ?", (agent_id,))
                evolution_count = cursor.fetchone()[0] or 0
                
                agents.append({
                    'agent_id': agent_id,
                    'first_seen': datetime.fromtimestamp(first_seen).isoformat() if first_seen else None,
                    'last_seen': datetime.fromtimestamp(last_seen).isoformat() if last_seen else None,
                    'memory_count': memory_count,
                    'memory_types': memory_types,
                    'evolution_count': evolution_count,
                    'activity_level': self._get_activity_level(memory_count, last_seen)
                })
            
            conn.close()
            return agents
            
        except Exception as e:
            return [{'error': str(e)}]
    
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
                SELECT old_traits, new_traits, trigger_event, timestamp
                FROM evolution_events
                WHERE agent_id = ?
                ORDER BY timestamp DESC
            """, (agent_id,))
            
            evolution_events = []
            for row in cursor.fetchall():
                old_traits, new_traits, trigger, timestamp = row
                try:
                    evolution_events.append({
                        'old_traits': json.loads(old_traits) if old_traits else {},
                        'new_traits': json.loads(new_traits) if new_traits else {},
                        'trigger': trigger,
                        'timestamp': datetime.fromtimestamp(timestamp).isoformat()
                    })
                except:
                    pass
            
            # Последние воспоминания
            cursor.execute("""
                SELECT memory_type, content, importance, timestamp, verification_count, success_rate
                FROM collective_memories
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT 20
            """, (agent_id,))
            
            recent_memories = []
            for row in cursor.fetchall():
                mem_type, content, importance, timestamp, verifications, success = row
                recent_memories.append({
                    'type': mem_type,
                    'content': content[:200] + "..." if len(content) > 200 else content,
                    'importance': importance,
                    'verifications': verifications,
                    'success_rate': success,
                    'timestamp': datetime.fromtimestamp(timestamp).isoformat()
                })
            
            conn.close()
            
            return {
                'agent_id': agent_id,
                'first_seen': datetime.fromtimestamp(first_seen).isoformat() if first_seen else None,
                'last_seen': datetime.fromtimestamp(last_seen).isoformat() if last_seen else None,
                'total_memories': total_memories,
                'memory_types': memory_types,
                'evolution_events': evolution_events,
                'recent_memories': recent_memories,
                'activity_level': self._get_activity_level(total_memories, last_seen)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_memory_analytics(self) -> Dict[str, Any]:
        """Аналитика по типам памяти"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Общая статистика по типам
            cursor.execute("""
                SELECT memory_type, COUNT(*), AVG(importance), AVG(success_rate)
                FROM collective_memories
                GROUP BY memory_type
                ORDER BY COUNT(*) DESC
            """)
            
            memory_stats = []
            for row in cursor.fetchall():
                mem_type, count, avg_importance, avg_success = row
                memory_stats.append({
                    'type': mem_type,
                    'count': count,
                    'avg_importance': avg_importance or 0,
                    'avg_success': avg_success or 0
                })
            
            # Активность по времени
            day_ago = (datetime.now() - timedelta(days=1)).timestamp()
            cursor.execute("""
                SELECT memory_type, COUNT(*)
                FROM collective_memories
                WHERE timestamp > ?
                GROUP BY memory_type
                ORDER BY COUNT(*) DESC
            """, (day_ago,))
            
            recent_activity = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'memory_stats': memory_stats,
                'recent_activity': recent_activity
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_activity_level(self, memory_count: int, last_seen: float) -> str:
        """Определение уровня активности"""
        if not last_seen:
            return "inactive"
        
        days_since_active = (datetime.now() - datetime.fromtimestamp(last_seen)).days
        
        if days_since_active > 7:
            return "inactive"
        elif memory_count > 100:
            return "very_high"
        elif memory_count > 50:
            return "high"
        elif memory_count > 20:
            return "medium"
        elif memory_count > 5:
            return "low"
        else:
            return "minimal"

# Инициализация анализатора
analyzer = CollectiveAnalyzer()

# HTML шаблон для дашборда
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧬 IKAR Collective Mind Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; 
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .stat-card h3 { font-size: 2em; margin-bottom: 10px; color: #4ade80; }
        .stat-card p { opacity: 0.8; }
        .section { 
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .section h2 { margin-bottom: 20px; color: #4ade80; }
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        .agent-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .agent-card:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
        }
        .agent-id { font-family: monospace; font-size: 0.9em; color: #60a5fa; }
        .agent-stats { margin-top: 10px; font-size: 0.9em; opacity: 0.8; }
        .activity-high { color: #4ade80; }
        .activity-medium { color: #fbbf24; }
        .activity-low { color: #f87171; }
        .activity-inactive { color: #9ca3af; }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
        }
        .modal-content {
            background: #1f2937;
            margin: 5% auto;
            padding: 20px;
            border-radius: 15px;
            width: 80%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: #fff; }
        .memory-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
        .memory-content { margin-top: 5px; font-style: italic; opacity: 0.8; }
        .refresh-btn {
            background: #4ade80;
            color: #1f2937;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .refresh-btn:hover { background: #22c55e; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 IKAR Collective Mind Dashboard</h1>
            <p>Мониторинг агентов коллективного разума в реальном времени</p>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">🔄 Обновить данные</button>
        
        <div class="stats-grid" id="overview-stats">
            <!-- Статистика будет загружена здесь -->
        </div>
        
        <div class="section">
            <h2>🤖 Агенты коллективного разума</h2>
            <div class="agents-grid" id="agents-list">
                <!-- Список агентов будет загружен здесь -->
            </div>
        </div>
        
        <div class="section">
            <h2>🧠 Аналитика памяти</h2>
            <div id="memory-analytics">
                <!-- Аналитика будет загружена здесь -->
            </div>
        </div>
    </div>
    
    <!-- Модальное окно для деталей агента -->
    <div id="agent-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div id="agent-details">
                <!-- Детали агента будут загружены здесь -->
            </div>
        </div>
    </div>
    
    <script>
        async function loadOverviewStats() {
            try {
                const response = await fetch('/api/overview');
                const data = await response.json();
                
                const statsHtml = `
                    <div class="stat-card">
                        <h3>${data.total_agents}</h3>
                        <p>Всего агентов</p>
                    </div>
                    <div class="stat-card">
                        <h3>${data.total_memories}</h3>
                        <p>Общих воспоминаний</p>
                    </div>
                    <div class="stat-card">
                        <h3>${data.total_evolution}</h3>
                        <p>Событий эволюции</p>
                    </div>
                    <div class="stat-card">
                        <h3>${data.active_day}</h3>
                        <p>Активных за 24ч</p>
                    </div>
                `;
                
                document.getElementById('overview-stats').innerHTML = statsHtml;
            } catch (error) {
                console.error('Ошибка загрузки статистики:', error);
            }
        }
        
        async function loadAgentsList() {
            try {
                const response = await fetch('/api/agents');
                const agents = await response.json();
                
                const agentsHtml = agents.map(agent => `
                    <div class="agent-card" onclick="showAgentDetails('${agent.agent_id}')">
                        <div class="agent-id">${agent.agent_id}</div>
                        <div class="agent-stats">
                            <div>Воспоминаний: ${agent.memory_count}</div>
                            <div>Эволюций: ${agent.evolution_count}</div>
                            <div class="activity-${agent.activity_level}">
                                Активность: ${agent.activity_level}
                            </div>
                        </div>
                    </div>
                `).join('');
                
                document.getElementById('agents-list').innerHTML = agentsHtml;
            } catch (error) {
                console.error('Ошибка загрузки агентов:', error);
            }
        }
        
        async function loadMemoryAnalytics() {
            try {
                const response = await fetch('/api/memory-analytics');
                const data = await response.json();
                
                const analyticsHtml = `
                    <h3>Статистика по типам памяти:</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                        ${data.memory_stats.map(stat => `
                            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;">
                                <strong>${stat.type}</strong><br>
                                Количество: ${stat.count}<br>
                                Средняя важность: ${stat.avg_importance.toFixed(2)}<br>
                                Средняя успешность: ${stat.avg_success.toFixed(2)}
                            </div>
                        `).join('')}
                    </div>
                `;
                
                document.getElementById('memory-analytics').innerHTML = analyticsHtml;
            } catch (error) {
                console.error('Ошибка загрузки аналитики:', error);
            }
        }
        
        async function showAgentDetails(agentId) {
            try {
                const response = await fetch(`/api/agent/${agentId}`);
                const agent = await response.json();
                
                const detailsHtml = `
                    <h2>🤖 Агент: ${agent.agent_id}</h2>
                    <p><strong>Первое появление:</strong> ${agent.first_seen}</p>
                    <p><strong>Последняя активность:</strong> ${agent.last_seen}</p>
                    <p><strong>Всего воспоминаний:</strong> ${agent.total_memories}</p>
                    <p><strong>Уровень активности:</strong> ${agent.activity_level}</p>
                    
                    <h3>Типы воспоминаний:</h3>
                    <div style="margin-bottom: 20px;">
                        ${Object.entries(agent.memory_types).map(([type, count]) => 
                            `<span style="background: rgba(255,255,255,0.1); padding: 5px 10px; margin: 5px; border-radius: 5px;">
                                ${type}: ${count}
                            </span>`
                        ).join('')}
                    </div>
                    
                    <h3>Последние воспоминания:</h3>
                    <div style="max-height: 300px; overflow-y: auto;">
                        ${agent.recent_memories.map(memory => `
                            <div class="memory-item">
                                <strong>${memory.type}</strong> (${memory.timestamp})<br>
                                <div class="memory-content">${memory.content}</div>
                                <small>Важность: ${memory.importance} | Успешность: ${memory.success_rate}</small>
                            </div>
                        `).join('')}
                    </div>
                `;
                
                document.getElementById('agent-details').innerHTML = detailsHtml;
                document.getElementById('agent-modal').style.display = 'block';
            } catch (error) {
                console.error('Ошибка загрузки деталей агента:', error);
            }
        }
        
        function closeModal() {
            document.getElementById('agent-modal').style.display = 'none';
        }
        
        function refreshData() {
            loadOverviewStats();
            loadAgentsList();
            loadMemoryAnalytics();
        }
        
        // Закрытие модального окна при клике вне его
        window.onclick = function(event) {
            const modal = document.getElementById('agent-modal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        
        // Загрузка данных при загрузке страницы
        window.onload = function() {
            refreshData();
            // Автообновление каждые 30 секунд
            setInterval(refreshData, 30000);
        };
    </script>
</body>
</html>
"""

# API эндпоинты
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Главная страница дашборда"""
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/api/overview")
async def get_overview():
    """Получение общей статистики"""
    return JSONResponse(content=analyzer.get_overview_stats())

@app.get("/api/agents")
async def get_agents():
    """Получение списка агентов"""
    return JSONResponse(content=analyzer.get_agents_list())

@app.get("/api/agent/{agent_id}")
async def get_agent_details(agent_id: str):
    """Получение деталей агента"""
    return JSONResponse(content=analyzer.get_agent_details(agent_id))

@app.get("/api/memory-analytics")
async def get_memory_analytics():
    """Получение аналитики памяти"""
    return JSONResponse(content=analyzer.get_memory_analytics())

if __name__ == "__main__":
    print("🌐 Запуск веб-дашборда коллективного разума IKAR")
    print("📊 Доступен по адресу: http://localhost:8080")
    
    uvicorn.run(app, host="0.0.0.0", port=8080) 