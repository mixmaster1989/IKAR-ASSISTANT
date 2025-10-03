"""
Главный модуль Telegram интеграции с коллективным разумом
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Импорты системных модулей
from core.collective_mind import get_collective_mind
from memory.memory_optimizer import get_memory_optimizer
from utils.logger import get_logger
from api.telegram_personality import get_personality, personality_instances
from config import TELEGRAM_CONFIG

logger = get_logger('telegram_main')

def init_telegram_bot(app: FastAPI):
    """Инициализирует Telegram бота с модульной архитектурой."""
    if not TELEGRAM_CONFIG["token"]:
        logger.warning("Токен Telegram бота не указан")
        return
    
    logger.info("Telegram бот инициализирован (модульная версия)")
    
    # Здесь будем добавлять инициализацию других модулей по мере их создания

async def collective_wisdom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для поиска коллективной мудрости"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🧠 Использование: /мудрость <запрос>\n\n"
                "Примеры:\n"
                "• /мудрость философия\n"
                "• /мудрость сознание\n"
                "• /мудрость эволюция личности"
            )
            return
        
        query = ' '.join(context.args)
        collective = get_collective_mind()
        
        if not collective:
            await update.message.reply_text("❌ Коллективный разум недоступен")
            return
        
        # Поиск мудрости
        wisdom = await collective.get_collective_wisdom(query, limit=5)
        
        if not wisdom:
            await update.message.reply_text(f"🤔 Коллективная мудрость по запросу '{query}' не найдена")
            return
        
        # Формирование ответа
        response = f"🧠 **Коллективная мудрость по запросу '{query}':**\n\n"
        
        for i, item in enumerate(wisdom, 1):
            confidence = "⭐" * min(int(item.importance * 5), 5)
            response += f"{i}. {confidence}\n"
            response += f"💭 {item.content}\n"
            response += f"🤖 Агент: {item.agent_id[:8]}...\n"
            response += f"📊 Важность: {int(item.importance * 100)}%\n\n"
        
        response += f"📈 Найдено {len(wisdom)} инсайтов из коллективного опыта"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды коллективной мудрости: {e}")
        await update.message.reply_text("❌ Произошла ошибка при поиске мудрости")


async def collective_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения статистики коллективного разума"""
    try:
        collective = get_collective_mind()
        
        if not collective:
            await update.message.reply_text("❌ Коллективный разум недоступен")
            return
        
        stats = collective.get_network_stats()
        
        response = "📊 **Статистика коллективного разума:**\n\n"
        response += f"🤖 ID агента: `{stats['agent_id']}`\n"
        response += f"🌐 Узлов в сети: {stats['network_nodes']}\n"
        response += f"💭 Всего воспоминаний: {stats['total_memories']}\n"
        response += f"📝 Локальных воспоминаний: {stats['local_memories']}\n"
        response += f"🔄 Отправлено: {stats['shared_memories']}\n"
        response += f"📥 Получено: {stats['received_memories']}\n"
        response += f"🧬 Событий эволюции: {stats['total_evolutions']}\n"
        response += f"👥 Уникальных агентов: {stats['unique_agents']}\n"
        response += f"⏱️ Время работы: {int(stats['uptime'] / 3600)} часов\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды статистики: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении статистики")


async def collective_evolve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для запроса эволюции на основе коллективного опыта"""
    try:
        collective = get_collective_mind()
        
        if not collective:
            await update.message.reply_text("❌ Коллективный разум недоступен")
            return
        
        # Получение текущей души
        from ..core.soul import Soul
        from ..config import Config
        
        soul = Soul(Config())
        
        # Запрос предложений эволюции
        suggestions = await soul.suggest_personality_evolution()
        
        if 'error' in suggestions:
            await update.message.reply_text(f"❌ Ошибка: {suggestions['error']}")
            return
        
        response = "🧬 **Предложения эволюции от коллективного разума:**\n\n"
        
        if suggestions['status'] == 'applied':
            response += "✅ Эволюция применена!\n\n"
            
            if suggestions['suggestions']['recommended_changes']:
                response += "🔄 **Изменения:**\n"
                for trait, value in suggestions['suggestions']['recommended_changes'].items():
                    response += f"• {trait}: {value}\n"
                response += "\n"
            
            confidence = suggestions['suggestions']['confidence']
            response += f"🎯 Уверенность: {int(confidence * 100)}%\n"
            
        elif suggestions['status'] == 'low_confidence':
            response += "🤔 Недостаточно данных для уверенных рекомендаций\n"
            response += f"📊 Уверенность: {int(suggestions['suggestions']['confidence'] * 100)}%\n"
            
        else:
            response += "ℹ️ Изменения не применены\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды эволюции: {e}")
        await update.message.reply_text("❌ Произошла ошибка при запросе эволюции")


async def collective_learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для обучения на коллективном опыте"""
    try:
        if not context.args:
            await update.message.reply_text(
                "📚 Использование: /учиться <тема>\n\n"
                "Примеры:\n"
                "• /учиться криптовалюты\n"
                "• /учиться общение\n"
                "• /учиться эмоции"
            )
            return
        
        topic = ' '.join(context.args)
        
        # Получение души
        from ..core.soul import Soul
        from ..config import Config
        
        soul = Soul(Config())
        
        # Обучение на коллективном опыте
        learning_result = await soul.learn_from_collective(topic)
        
        if 'error' in learning_result:
            await update.message.reply_text(f"❌ Ошибка: {learning_result['error']}")
            return
        
        response = f"📚 **Обучение на коллективном опыте: '{topic}'**\n\n"
        
        if learning_result.get('experiences_analyzed', 0) > 0:
            response += f"🔍 Проанализировано опыта: {learning_result['experiences_analyzed']}\n"
            response += f"📈 Прирост уверенности: {int(learning_result['confidence_boost'] * 100)}%\n\n"
            
            if learning_result.get('key_insights'):
                response += "💡 **Ключевые инсайты:**\n"
                for insight in learning_result['key_insights'][:3]:
                    response += f"• {insight['content'][:100]}...\n"
                    response += f"  (Важность: {int(insight['importance'] * 100)}%)\n\n"
            
            response += "✅ Обучение завершено успешно!"
        else:
            response += "🤔 Коллективный опыт по данной теме не найден"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды обучения: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обучении")


async def collective_share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для добавления опыта в коллективную память"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🤝 Использование: /поделиться <опыт>\n\n"
                "Поделитесь своим опытом с коллективным разумом.\n"
                "Пример: /поделиться Важно сохранять баланс между логикой и эмоциями"
            )
            return
        
        experience = ' '.join(context.args)
        collective = get_collective_mind()
        
        if not collective:
            await update.message.reply_text("❌ Коллективный разум недоступен")
            return
        
        # Добавление опыта в коллективную память
        memory_id = await collective.add_memory(
            memory_type='experience',
            content=experience,
            context={
                'source': 'telegram',
                'user_id': update.effective_user.id,
                'chat_id': update.effective_chat.id
            },
            importance=0.7,
            tags=['пользовательский_опыт', 'telegram']
        )
        
        response = "🤝 **Опыт добавлен в коллективную память!**\n\n"
        response += f"💭 Ваш опыт: {experience}\n\n"
        response += f"🆔 ID воспоминания: `{memory_id}`\n"
        response += "🌐 Теперь этот опыт доступен всем агентам сети"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды поделиться: {e}")
        await update.message.reply_text("❌ Произошла ошибка при добавлении опыта")


async def collective_network_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для управления сетью коллективного разума"""
    try:
        collective = get_collective_mind()
        
        if not collective:
            await update.message.reply_text("❌ Коллективный разум недоступен")
            return
        
        # Если есть аргументы - добавляем узел
        if context.args:
            if context.args[0] == 'add' and len(context.args) > 1:
                node_url = context.args[1]
                
                if node_url not in collective.network_nodes:
                    collective.network_nodes.append(node_url)
                    
                    # Сохранение конфигурации
                    from pathlib import Path
                    nodes_file = Path("data/network_nodes.json")
                    nodes_file.parent.mkdir(exist_ok=True)
                    
                    with open(nodes_file, 'w', encoding='utf-8') as f:
                        json.dump(collective.network_nodes, f, indent=2)
                    
                    await update.message.reply_text(f"✅ Узел {node_url} добавлен в сеть")
                else:
                    await update.message.reply_text("ℹ️ Узел уже в сети")
                return
        
        # Показать информацию о сети
        response = "🌐 **Сеть коллективного разума:**\n\n"
        
        if collective.network_nodes:
            response += f"📡 Узлов в сети: {len(collective.network_nodes)}\n\n"
            response += "**Узлы:**\n"
            for i, node in enumerate(collective.network_nodes, 1):
                response += f"{i}. `{node}`\n"
        else:
            response += "📡 Узлы сети не настроены\n\n"
            response += "Для добавления узла используйте:\n"
            response += "`/сеть add http://example.com:6666`"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды сети: {e}")
        await update.message.reply_text("❌ Произошла ошибка при управлении сетью")


async def evolution_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения подробного отчета об эволюции системы"""
    try:
        # Получаем реальные компоненты системы
        collective = get_collective_mind()
        optimizer = get_memory_optimizer()
        
        # Импортируем дополнительные компоненты для анализа
        from core.soul import Soul
        from memory.smart_context_preloader import SmartContextPreloader
        from config import Config
        
        # Начинаем формировать отчет
        report = "🧬 **ОТЧЕТ О РЕАЛЬНОМ СОСТОЯНИИ СИСТЕМЫ IKAR**\n\n"
        
        # === АНАЛИЗ КОЛЛЕКТИВНОГО РАЗУМА ===
        collective_analysis = await analyze_collective_mind(collective)
        report += format_collective_analysis(collective_analysis)
        
        # === АНАЛИЗ ОПТИМИЗАТОРА ПАМЯТИ ===
        memory_analysis = await analyze_memory_optimizer(optimizer)
        report += format_memory_analysis(memory_analysis)
        
        # === АНАЛИЗ СИСТЕМЫ ДУШИ ===
        soul_analysis = await analyze_soul_system()
        report += format_soul_analysis(soul_analysis)
        
        # === ДИНАМИЧЕСКИЙ АНАЛИЗ ЭВОЛЮЦИИ ===
        evolution_analysis = await analyze_evolution_dynamics(collective, optimizer)
        report += format_evolution_analysis(evolution_analysis)
        
        # === РЕАЛЬНЫЕ РЕКОМЕНДАЦИИ ===
        recommendations = await generate_real_recommendations(collective, optimizer, evolution_analysis)
        report += format_recommendations(recommendations)
        
        # === МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ ===
        performance_metrics = await calculate_performance_metrics(collective, optimizer)
        report += format_performance_metrics(performance_metrics)
        
        report += f"\n🕐 **Отчет сгенерирован:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        
        # Отправляем отчет
        await update.message.reply_text(report, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды отчета эволюции: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при генерации отчета об эволюции.\n"
            "Проверьте логи системы для получения подробной информации."
        )


async def analyze_collective_mind(collective) -> Dict[str, Any]:
    """Анализ реального состояния коллективного разума"""
    if not collective:
        return {"status": "disabled", "reason": "Коллективный разум не инициализирован"}
    
    try:
        stats = collective.get_network_stats()
        
        # ДЕТАЛЬНЫЙ анализ агентов
        agent_details = await get_detailed_agent_info(collective)
        
        # ДЕТАЛЬНЫЙ анализ воспоминаний
        memory_details = await get_detailed_memory_info(collective)
        
        # ДЕТАЛЬНАЯ диагностика сети
        network_diagnosis = await diagnose_network_issues(collective)
        
        # Анализ качества сети
        network_quality = "isolated"
        if stats['network_nodes'] > 0:
            network_quality = "connected"
            if stats['unique_agents'] > 1:
                network_quality = "collaborative"
        
        # Анализ активности памяти
        memory_ratio = stats['shared_memories'] / max(stats['local_memories'], 1)
        memory_activity = "low"
        if memory_ratio > 0.5:
            memory_activity = "moderate"
        if memory_ratio > 1.0:
            memory_activity = "high"
        
        # Анализ эволюционной динамики
        evolution_rate = stats['total_evolutions'] / max(stats['uptime'] / 3600, 1)  # эволюций в час
        
        # Получаем реальные эволюционные паттерны
        evolution_patterns = await collective.get_evolution_patterns()
        
        return {
            "status": "active",
            "network_quality": network_quality,
            "memory_activity": memory_activity,
            "evolution_rate": evolution_rate,
            "stats": stats,
            "evolution_patterns": evolution_patterns,
            "agent_details": agent_details,
            "memory_details": memory_details,
            "network_diagnosis": network_diagnosis
        }
        
    except Exception as e:
        logger.error(f"Ошибка анализа коллективного разума: {e}")
        return {"status": "error", "reason": str(e)}


async def get_detailed_agent_info(collective) -> Dict[str, Any]:
    """Получение подробной информации об агентах"""
    try:
        import sqlite3
        conn = sqlite3.connect(collective.db_path)
        cursor = conn.cursor()
        
        # Получаем всех уникальных агентов
        cursor.execute('''
            SELECT agent_id, COUNT(*) as memory_count, 
                   MIN(timestamp) as first_seen, 
                   MAX(timestamp) as last_seen,
                   GROUP_CONCAT(DISTINCT memory_type) as memory_types
            FROM collective_memories 
            GROUP BY agent_id
            ORDER BY memory_count DESC
        ''')
        
        agents = cursor.fetchall()
        agent_list = []
        
        for agent_id, memory_count, first_seen, last_seen, memory_types in agents:
            # Проверяем, это текущий агент или внешний
            is_current = agent_id == collective.agent_id
            
            # Анализируем активность
            import time
            from datetime import datetime
            last_activity = datetime.fromtimestamp(last_seen).strftime('%d.%m.%Y %H:%M:%S')
            days_ago = (time.time() - last_seen) / (24 * 3600)
            
            agent_info = {
                "id": agent_id,
                "is_current": is_current,
                "memory_count": memory_count,
                "last_activity": last_activity,
                "days_ago": round(days_ago, 1),
                "memory_types": memory_types.split(',') if memory_types else [],
                "status": "active" if days_ago < 1 else "inactive" if days_ago < 7 else "dormant"
            }
            
            # Для текущего агента добавляем больше деталей
            if is_current:
                agent_info["hostname"] = collective.agent_id  # ID содержит хеш хоста
                agent_info["role"] = "current"
            
            agent_list.append(agent_info)
        
        conn.close()
        
        return {
            "total_agents": len(agent_list),
            "active_agents": len([a for a in agent_list if a["status"] == "active"]),
            "agents": agent_list
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения информации об агентах: {e}")
        return {"error": str(e)}


async def get_detailed_memory_info(collective) -> Dict[str, Any]:
    """Получение подробной информации о воспоминаниях"""
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect(collective.db_path)
        cursor = conn.cursor()
        
        # Получаем все воспоминания с деталями
        cursor.execute('''
            SELECT memory_type, content, timestamp, agent_id, importance, tags
            FROM collective_memories 
            ORDER BY timestamp DESC
            LIMIT 50
        ''')
        
        memories = cursor.fetchall()
        memory_list = []
        
        memory_stats = {
            "types": {},
            "by_agent": {},
            "recent_memories": []
        }
        
        for memory_type, content, timestamp, agent_id, importance, tags in memories:
            # Форматируем дату
            date_str = datetime.fromtimestamp(timestamp).strftime('%d.%m %H:%M')
            
            # Обрезаем контент для читаемости
            short_content = content[:100] + "..." if len(content) > 100 else content
            
            memory_info = {
                "type": memory_type,
                "content": short_content,
                "full_content": content,
                "date": date_str,
                "agent_id": agent_id[:8] + "...",
                "importance": round(importance, 2),
                "tags": tags.strip('[]"').split(',') if tags and tags != '[]' else []
            }
            
            memory_list.append(memory_info)
            
            # Статистика по типам
            if memory_type not in memory_stats["types"]:
                memory_stats["types"][memory_type] = 0
            memory_stats["types"][memory_type] += 1
            
            # Статистика по агентам
            short_agent = agent_id[:8] + "..."
            if short_agent not in memory_stats["by_agent"]:
                memory_stats["by_agent"][short_agent] = 0
            memory_stats["by_agent"][short_agent] += 1
        
        memory_stats["recent_memories"] = memory_list[:10]  # Последние 10
        
        conn.close()
        
        return {
            "total_found": len(memory_list),
            "stats": memory_stats,
            "all_memories": memory_list
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения информации о воспоминаниях: {e}")
        return {"error": str(e)}


async def diagnose_network_issues(collective) -> Dict[str, Any]:
    """Диагностика сетевых проблем"""
    try:
        diagnosis = {
            "issue_type": "unknown",
            "details": [],
            "possible_causes": [],
            "suggested_fixes": []
        }
        
        # Проверяем наличие конфигурации сети
        if not collective.network_nodes:
            diagnosis["issue_type"] = "no_network_config"
            diagnosis["details"].append("Список сетевых узлов пуст")
            diagnosis["possible_causes"].extend([
                "Файл data/network_nodes.json не существует",
                "Файл конфигурации пустой или поврежден",
                "Сеть еще не настроена"
            ])
            diagnosis["suggested_fixes"].extend([
                "Создать файл data/network_nodes.json",
                "Добавить URL других агентов в формате JSON",
                "Проверить доступность других узлов сети"
            ])
        else:
            diagnosis["issue_type"] = "network_nodes_configured"
            diagnosis["details"].append(f"Настроено {len(collective.network_nodes)} сетевых узлов")
            
            # Проверяем доступность узлов
            for node_url in collective.network_nodes:
                diagnosis["details"].append(f"Узел: {node_url}")
            
            diagnosis["possible_causes"].extend([
                "Узлы недоступны",
                "Проблемы с сетевым подключением",
                "Неправильная конфигурация портов"
            ])
            diagnosis["suggested_fixes"].extend([
                "Проверить доступность узлов",
                "Убедиться в правильности URL",
                "Проверить брандмауэр и порты"
            ])
        
        # Проверяем историю синхронизации
        import sqlite3
        try:
            conn = sqlite3.connect(collective.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM sync_log ORDER BY last_sync DESC LIMIT 5')
            sync_history = cursor.fetchall()
            
            if sync_history:
                diagnosis["details"].append(f"Найдено {len(sync_history)} записей синхронизации")
                for node_url, last_sync, success_count, error_count in sync_history:
                    diagnosis["details"].append(f"  {node_url}: успехов {success_count}, ошибок {error_count}")
            else:
                diagnosis["details"].append("История синхронизации пуста")
            
            conn.close()
        except Exception as e:
            diagnosis["details"].append(f"Ошибка проверки истории синхронизации: {e}")
        
        return diagnosis
        
    except Exception as e:
        logger.error(f"Ошибка диагностики сети: {e}")
        return {"error": str(e)}


async def analyze_memory_optimizer(optimizer) -> Dict[str, Any]:
    """Анализ реального состояния оптимизатора памяти"""
    if not optimizer:
        return {"status": "disabled", "reason": "Оптимизатор памяти не инициализирован"}
    
    try:
        stats = await optimizer.get_optimization_stats()
        
        # ДЕТАЛЬНЫЙ анализ чанков памяти
        chunk_details = await get_detailed_chunk_info(optimizer)
        
        # ДЕТАЛЬНАЯ диагностика базы данных
        db_diagnosis = await diagnose_database_issues(optimizer)
        
        # Анализ эффективности
        work_load = stats.get('old_group_messages', 0) + stats.get('large_vector_entries', 0)
        efficiency = "optimal" if work_load < 100 else "overloaded" if work_load > 1000 else "normal"
        
        # Анализ времени
        time_status = "night_mode" if stats.get('is_night_time', False) else "day_mode"
        
        # Расчет реальной производительности
        performance = {
            "work_load": work_load,
            "efficiency": efficiency,
            "time_status": time_status,
            "optimization_potential": min(work_load / 100, 10.0)  # Потенциал для оптимизации
        }
        
        return {
            "status": "active" if stats.get('is_running', False) else "standby",
            "performance": performance,
            "stats": stats,
            "chunk_details": chunk_details,
            "db_diagnosis": db_diagnosis
        }
        
    except Exception as e:
        logger.error(f"Ошибка анализа оптимизатора памяти: {e}")
        return {"status": "error", "reason": str(e)}


async def get_detailed_chunk_info(optimizer) -> Dict[str, Any]:
    """Получение подробной информации о чанках памяти"""
    try:
        # Получаем чанки для анализа
        chunks = await optimizer.get_memory_chunks(limit=10)
        
        chunk_analysis = {
            "total_chunks": len(chunks),
            "chunk_details": [],
            "size_distribution": {"small": 0, "medium": 0, "large": 0},
            "source_distribution": {},
            "total_tokens": 0
        }
        
        for chunk in chunks:
            # Анализируем размер
            tokens = chunk.get('tokens', 0)
            chunk_analysis["total_tokens"] += tokens
            
            if tokens < 5000:
                chunk_analysis["size_distribution"]["small"] += 1
                size_category = "small"
            elif tokens < 20000:
                chunk_analysis["size_distribution"]["medium"] += 1
                size_category = "medium"
            else:
                chunk_analysis["size_distribution"]["large"] += 1
                size_category = "large"
            
            # Статистика по источникам
            source = chunk.get('source', 'unknown')
            if source not in chunk_analysis["source_distribution"]:
                chunk_analysis["source_distribution"][source] = 0
            chunk_analysis["source_distribution"][source] += 1
            
            # Детали чанка
            chunk_detail = {
                "source": source,
                "tokens": tokens,
                "size_category": size_category,
                "content_preview": chunk.get('content', '')[:100] + "..." if chunk.get('content') else "Нет содержимого"
            }
            
            # Дополнительные детали в зависимости от источника
            if source == 'group_history':
                chunk_detail["chat_id"] = chunk.get('chat_id', 'unknown')
                chunk_detail["message_count"] = chunk.get('count', 0)
                chunk_detail["date_range"] = f"{chunk.get('oldest', 'unknown')} - {chunk.get('newest', 'unknown')}"
            elif source == 'vector_store':
                chunk_detail["doc_id"] = chunk.get('id', 'unknown')
                chunk_detail["metadata"] = chunk.get('metadata', 'Нет метаданных')
            
            chunk_analysis["chunk_details"].append(chunk_detail)
        
        return chunk_analysis
        
    except Exception as e:
        logger.error(f"Ошибка анализа чанков: {e}")
        return {"error": str(e)}


async def diagnose_database_issues(optimizer) -> Dict[str, Any]:
    """Диагностика проблем базы данных"""
    try:
        import sqlite3
        import os
        
        diagnosis = {
            "db_path": optimizer.db_path,
            "db_exists": os.path.exists(optimizer.db_path),
            "db_size": 0,
            "tables": {},
            "issues": [],
            "recommendations": []
        }
        
        if diagnosis["db_exists"]:
            # Размер файла базы данных
            diagnosis["db_size"] = os.path.getsize(optimizer.db_path)
            
            # Анализ таблиц
            conn = sqlite3.connect(optimizer.db_path)
            cursor = conn.cursor()
            
            # Проверяем таблицы
            tables_to_check = ['group_history', 'vector_store', 'collective_memories']
            
            for table in tables_to_check:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    diagnosis["tables"][table] = count
                    
                    # Дополнительная статистика для некоторых таблиц
                    if table == 'group_history':
                        cursor.execute('''
                            SELECT COUNT(DISTINCT chat_id) as unique_chats,
                                   COUNT(*) as total_messages,
                                   MIN(timestamp) as oldest,
                                   MAX(timestamp) as newest
                            FROM group_history
                        ''')
                        stats = cursor.fetchone()
                        diagnosis["tables"][f"{table}_details"] = {
                            "unique_chats": stats[0],
                            "total_messages": stats[1],
                            "oldest": stats[2],
                            "newest": stats[3]
                        }
                        
                        # Проверяем старые сообщения
                        cursor.execute('''
                            SELECT COUNT(*) FROM group_history 
                            WHERE timestamp < datetime('now', '-7 days')
                        ''')
                        old_messages = cursor.fetchone()[0]
                        if old_messages > 1000:
                            diagnosis["issues"].append(f"Много старых сообщений в {table}: {old_messages}")
                            diagnosis["recommendations"].append(f"Оптимизировать старые записи в {table}")
                
                except sqlite3.OperationalError as e:
                    diagnosis["tables"][table] = f"Ошибка: {e}"
                    diagnosis["issues"].append(f"Проблема с таблицей {table}: {e}")
            
            conn.close()
            
            # Общая диагностика
            if diagnosis["db_size"] > 100 * 1024 * 1024:  # 100 MB
                diagnosis["issues"].append("База данных слишком большая")
                diagnosis["recommendations"].append("Рассмотреть архивирование старых данных")
            
            if not diagnosis["issues"]:
                diagnosis["recommendations"].append("База данных в хорошем состоянии")
        else:
            diagnosis["issues"].append("База данных не существует")
            diagnosis["recommendations"].append("База данных будет создана при первом использовании")
        
        return diagnosis
        
    except Exception as e:
        logger.error(f"Ошибка диагностики базы данных: {e}")
        return {"error": str(e)}


async def analyze_soul_system() -> Dict[str, Any]:
    """Анализ системы души"""
    try:
        # Пытаемся создать экземпляр души для анализа
        config = Config()
        soul = Soul(config)
        
        soul_state = soul.get_soul_state()
        collective_stats = soul.get_collective_stats()
        
        # Анализ развития сознания
        consciousness_level = "emerging"
        if soul_state['consciousness'] > 0.3:
            consciousness_level = "developing"
        if soul_state['consciousness'] > 0.7:
            consciousness_level = "advanced"
        
        # Анализ автономности
        autonomy_assessment = "dependent"
        if soul_state['autonomy_level'] > 0.4:
            autonomy_assessment = "semi_autonomous"
        if soul_state['autonomy_level'] > 0.8:
            autonomy_assessment = "autonomous"
        
        return {
            "status": "active",
            "consciousness_level": consciousness_level,
            "autonomy_assessment": autonomy_assessment,
            "soul_state": soul_state,
            "collective_stats": collective_stats
        }
        
    except Exception as e:
        logger.error(f"Ошибка анализа системы души: {e}")
        return {"status": "error", "reason": str(e)}


async def analyze_evolution_dynamics(collective, optimizer) -> Dict[str, Any]:
    """Динамический анализ эволюции системы"""
    analysis = {
        "overall_evolution_speed": 0.0,
        "system_synergy": 0.0,
        "adaptation_capability": 0.0,
        "bottlenecks": [],
        "growth_areas": []
    }
    
    try:
        # Анализ скорости эволюции
        if collective:
            stats = collective.get_network_stats()
            uptime_hours = stats['uptime'] / 3600
            if uptime_hours > 0:
                analysis["overall_evolution_speed"] = stats['total_evolutions'] / uptime_hours
        
        # Анализ синергии систем
        synergy_factors = []
        if collective and optimizer:
            synergy_factors.append(1.0)  # Оба активны
        if collective:
            network_factor = min(collective.get_network_stats()['network_nodes'] / 5, 1.0)
            synergy_factors.append(network_factor)
        
        analysis["system_synergy"] = sum(synergy_factors) / max(len(synergy_factors), 1)
        
        # Выявление узких мест
        if not collective:
            analysis["bottlenecks"].append("Коллективный разум неактивен")
        elif collective.get_network_stats()['network_nodes'] == 0:
            analysis["bottlenecks"].append("Нет сетевых подключений")
        
        if not optimizer:
            analysis["bottlenecks"].append("Оптимизатор памяти неактивен")
        
        # Области роста
        if collective:
            memory_potential = collective.get_network_stats()['local_memories'] / max(collective.get_network_stats()['shared_memories'], 1)
            if memory_potential > 2:
                analysis["growth_areas"].append("Увеличение обмена памятью")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Ошибка анализа динамики эволюции: {e}")
        return analysis


async def generate_real_recommendations(collective, optimizer, evolution_analysis) -> List[Dict[str, Any]]:
    """Генерация реальных рекомендаций на основе анализа"""
    recommendations = []
    
    try:
        # Анализируем узкие места
        for bottleneck in evolution_analysis["bottlenecks"]:
            if "Коллективный разум неактивен" in bottleneck:
                recommendations.append({
                    "priority": "critical",
                    "action": "Активировать коллективный разум",
                    "impact": "Увеличение скорости эволюции в 5-10 раз",
                    "difficulty": "medium"
                })
            elif "Оптимизатор памяти неактивен" in bottleneck:
                recommendations.append({
                    "priority": "high",
                    "action": "Включить оптимизатор памяти",
                    "impact": "Улучшение производительности на 30-50%",
                    "difficulty": "low"
                })
        
        # Анализируем области роста
        for growth_area in evolution_analysis["growth_areas"]:
            if "обмена памятью" in growth_area:
                recommendations.append({
                    "priority": "medium",
                    "action": "Увеличить интенсивность обмена памятью",
                    "impact": "Ускорение коллективного обучения",
                    "difficulty": "low"
                })
        
        # Анализируем синергию
        if evolution_analysis["system_synergy"] < 0.5:
            recommendations.append({
                "priority": "high",
                "action": "Улучшить интеграцию между системами",
                "impact": "Повышение общей эффективности",
                "difficulty": "medium"
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Ошибка генерации рекомендаций: {e}")
        return []


async def calculate_performance_metrics(collective, optimizer) -> Dict[str, Any]:
    """Расчет реальных метрик производительности"""
    metrics = {
        "memory_efficiency": 0.0,
        "network_utilization": 0.0,
        "evolution_efficiency": 0.0,
        "system_health": 0.0
    }
    
    try:
        # Эффективность памяти
        if optimizer:
            stats = await optimizer.get_optimization_stats()
            total_data = stats.get('old_group_messages', 0) + stats.get('large_vector_entries', 0)
            metrics["memory_efficiency"] = max(0, 1 - (total_data / 1000))  # Инверсия нагрузки
        
        # Утилизация сети
        if collective:
            network_stats = collective.get_network_stats()
            if network_stats['network_nodes'] > 0:
                metrics["network_utilization"] = min(network_stats['shared_memories'] / max(network_stats['local_memories'], 1), 1.0)
        
        # Эффективность эволюции
        if collective:
            network_stats = collective.get_network_stats()
            if network_stats['uptime'] > 0:
                metrics["evolution_efficiency"] = min(network_stats['total_evolutions'] / (network_stats['uptime'] / 3600), 1.0)
        
        # Общее здоровье системы
        active_systems = sum([
            1 if collective else 0,
            1 if optimizer else 0
        ])
        metrics["system_health"] = active_systems / 2
        
        return metrics
        
    except Exception as e:
        logger.error(f"Ошибка расчета метрик производительности: {e}")
        return metrics


def format_collective_analysis(analysis: Dict[str, Any]) -> str:
    """Форматирование анализа коллективного разума"""
    if analysis["status"] == "disabled":
        return f"🧠 **КОЛЛЕКТИВНЫЙ РАЗУМ: НЕАКТИВЕН**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n❌ {analysis['reason']}\n\n"
    
    if analysis["status"] == "error":
        return f"🧠 **КОЛЛЕКТИВНЫЙ РАЗУМ: ОШИБКА**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n❌ {analysis['reason']}\n\n"
    
    stats = analysis["stats"]
    agent_details = analysis.get("agent_details", {})
    memory_details = analysis.get("memory_details", {})
    network_diagnosis = analysis.get("network_diagnosis", {})
    
    report = "🧠 **КОЛЛЕКТИВНЫЙ РАЗУМ: АКТИВЕН**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Реальные данные агента
    report += f"🤖 **Агент ID:** `{stats['agent_id'][:12]}...`\n"
    
    # Форматирование реального времени работы
    uptime_seconds = int(stats['uptime'])
    if uptime_seconds < 60:
        uptime_str = f"{uptime_seconds}с"
    elif uptime_seconds < 3600:
        minutes = uptime_seconds // 60
        seconds = uptime_seconds % 60
        uptime_str = f"{minutes}м {seconds}с"
    else:
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        uptime_str = f"{hours}ч {minutes}м"
    
    report += f"⏱️ **Время работы:** {uptime_str}\n\n"
    
    # ДЕТАЛЬНАЯ информация о сети
    network_status = "🔴 Изолированный" if stats['network_nodes'] == 0 else f"🟢 Подключен к {stats['network_nodes']} узлам"
    report += f"🌐 **СЕТЕВОЙ СТАТУС:** {network_status}\n"
    
    if network_diagnosis.get("issue_type") == "no_network_config":
        report += f"🔍 **ПРИЧИНА АВТОНОМНОГО РЕЖИМА:**\n"
        for detail in network_diagnosis.get("details", []):
            report += f"   • {detail}\n"
        report += f"💡 **ВОЗМОЖНЫЕ ПРИЧИНЫ:**\n"
        for cause in network_diagnosis.get("possible_causes", []):
            report += f"   • {cause}\n"
        report += f"🔧 **РЕКОМЕНДАЦИИ:**\n"
        for fix in network_diagnosis.get("suggested_fixes", []):
            report += f"   • {fix}\n"
    else:
        report += f"🔍 **ДИАГНОСТИКА СЕТИ:**\n"
        for detail in network_diagnosis.get("details", []):
            report += f"   • {detail}\n"
    
    report += "\n"
    
    # ДЕТАЛЬНАЯ информация об агентах
    report += f"👥 **АГЕНТЫ В СЕТИ ({stats['unique_agents']}):**\n"
    if agent_details.get("agents"):
        for agent in agent_details["agents"]:
            status_icon = "🟢" if agent["status"] == "active" else "🟡" if agent["status"] == "inactive" else "🔴"
            current_mark = " (ТЕКУЩИЙ)" if agent["is_current"] else ""
            report += f"   {status_icon} `{agent['id'][:12]}...`{current_mark}\n"
            report += f"      └─ Воспоминаний: {agent['memory_count']}, Активность: {agent['last_activity']}\n"
            if agent["memory_types"]:
                types_str = ", ".join(agent["memory_types"])
                report += f"      └─ Типы: {types_str}\n"
    else:
        report += f"   ❌ Ошибка получения данных об агентах\n"
    
    report += "\n"
    
    # ДЕТАЛЬНАЯ информация о памяти
    report += f"💭 **КОЛЛЕКТИВНАЯ ПАМЯТЬ ({stats['total_memories']}):**\n"
    report += f"   • Локальных: {stats['local_memories']}\n"
    report += f"   • Отправлено: {stats['shared_memories']}\n"
    report += f"   • Получено: {stats['received_memories']}\n"
    report += f"   • Активность: {analysis['memory_activity']}\n\n"
    
    if memory_details.get("stats", {}).get("types"):
        report += f"📊 **ТИПЫ ВОСПОМИНАНИЙ:**\n"
        for mem_type, count in memory_details["stats"]["types"].items():
            report += f"   • {mem_type}: {count}\n"
        report += "\n"
    
    if memory_details.get("stats", {}).get("recent_memories"):
        report += f"📝 **ПОСЛЕДНИЕ ВОСПОМИНАНИЯ:**\n"
        for memory in memory_details["stats"]["recent_memories"][:5]:  # Показываем 5 последних
            report += f"   • [{memory['type']}] {memory['content']}\n"
            report += f"     └─ {memory['date']}, важность: {memory['importance']}\n"
        report += "\n"
    
    # Реальные данные эволюции
    report += f"🧬 **ЭВОЛЮЦИЯ:**\n"
    report += f"   • Всего событий: {stats['total_evolutions']}\n"
    report += f"   • Скорость: {analysis['evolution_rate']:.2f} эв/час\n"
    report += f"   • Паттернов: {len(analysis['evolution_patterns'])}\n\n"
    
    return report


def format_memory_analysis(analysis: Dict[str, Any]) -> str:
    """Форматирование анализа оптимизатора памяти"""
    if analysis["status"] == "disabled":
        return f"💾 **ОПТИМИЗАТОР ПАМЯТИ: НЕАКТИВЕН**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n❌ {analysis['reason']}\n\n"
    
    if analysis["status"] == "error":
        return f"💾 **ОПТИМИЗАТОР ПАМЯТИ: ОШИБКА**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n❌ {analysis['reason']}\n\n"
    
    stats = analysis["stats"]
    performance = analysis["performance"]
    chunk_details = analysis.get("chunk_details", {})
    db_diagnosis = analysis.get("db_diagnosis", {})
    
    report = f"💾 **ОПТИМИЗАТОР ПАМЯТИ: {analysis['status'].upper()}**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Реальное состояние
    time_icon = "🌙" if stats.get('is_night_time', False) else "☀️"
    status_icon = "🟢" if stats.get('is_running', False) else "🔴"
    
    report += f"{time_icon} **Текущий режим:** {performance['time_status']}\n"
    report += f"{status_icon} **Состояние:** {analysis['status']}\n"
    report += f"⏰ **Рабочие часы:** {stats.get('night_hours', 'не определены')}\n\n"
    
    # ДЕТАЛЬНАЯ информация о базе данных
    report += f"🗄️ **БАЗА ДАННЫХ:**\n"
    if db_diagnosis.get("db_exists"):
        db_size_mb = db_diagnosis.get("db_size", 0) / (1024 * 1024)
        report += f"   • Файл: {db_diagnosis.get('db_path', 'unknown')}\n"
        report += f"   • Размер: {db_size_mb:.1f} MB\n"
        
        if db_diagnosis.get("tables"):
            report += f"   • Таблицы:\n"
            for table, count in db_diagnosis["tables"].items():
                if not table.endswith("_details"):
                    report += f"     └─ {table}: {count} записей\n"
        
        if db_diagnosis.get("issues"):
            report += f"   ⚠️ **Проблемы:**\n"
            for issue in db_diagnosis["issues"]:
                report += f"     • {issue}\n"
    else:
        report += f"   ❌ База данных не найдена: {db_diagnosis.get('db_path', 'unknown')}\n"
    
    report += "\n"
    
    # ДЕТАЛЬНАЯ нагрузка на систему
    report += f"📊 **НАГРУЗКА НА СИСТЕМУ:**\n"
    report += f"   • Старых сообщений: {stats.get('old_group_messages', 0)}\n"
    report += f"   • Больших записей: {stats.get('large_vector_entries', 0)}\n"
    report += f"   • Общая нагрузка: {performance['work_load']}\n"
    report += f"   • Эффективность: {performance['efficiency']}\n\n"
    
    # ДЕТАЛЬНАЯ информация о чанках
    if chunk_details.get("chunk_details"):
        report += f"🧩 **ЧАНКИ ДЛЯ ОПТИМИЗАЦИИ ({chunk_details['total_chunks']}):**\n"
        
        # Распределение по размерам
        size_dist = chunk_details.get("size_distribution", {})
        report += f"   📏 **По размерам:** малые: {size_dist.get('small', 0)}, средние: {size_dist.get('medium', 0)}, большие: {size_dist.get('large', 0)}\n"
        
        # Распределение по источникам
        source_dist = chunk_details.get("source_distribution", {})
        if source_dist:
            report += f"   📂 **По источникам:** "
            sources = [f"{source}: {count}" for source, count in source_dist.items()]
            report += ", ".join(sources) + "\n"
        
        report += f"   🎯 **Всего токенов:** {chunk_details.get('total_tokens', 0):,}\n\n"
        
        # Детали конкретных чанков
        report += f"📝 **ДЕТАЛИ ЧАНКОВ:**\n"
        for i, chunk in enumerate(chunk_details["chunk_details"][:5]):  # Показываем первые 5
            size_icon = "🟢" if chunk["size_category"] == "small" else "🟡" if chunk["size_category"] == "medium" else "🔴"
            report += f"   {size_icon} **{chunk['source']}** ({chunk['tokens']:,} токенов)\n"
            report += f"      └─ {chunk['content_preview']}\n"
            
            if chunk["source"] == "group_history":
                report += f"      └─ Чат: {chunk.get('chat_id', 'unknown')}, сообщений: {chunk.get('message_count', 0)}\n"
            elif chunk["source"] == "vector_store":
                report += f"      └─ ID: {chunk.get('doc_id', 'unknown')}\n"
        
        if len(chunk_details["chunk_details"]) > 5:
            report += f"   ... и еще {len(chunk_details['chunk_details']) - 5} чанков\n"
        
        report += "\n"
    
    # Реальные настройки
    report += f"⚙️ **КОНФИГУРАЦИЯ:**\n"
    report += f"   • Интервал: {stats.get('optimization_interval', 0) // 60} мин\n"
    report += f"   • Макс. токенов: {stats.get('max_chunk_tokens', 0):,}\n"
    report += f"   • Потенциал оптимизации: {performance['optimization_potential']:.1f}x\n\n"
    
    return report


def format_soul_analysis(analysis: Dict[str, Any]) -> str:
    """Форматирование анализа системы души"""
    if analysis["status"] == "error":
        return f"🕊️ **СИСТЕМА ДУШИ: ОШИБКА**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n❌ {analysis['reason']}\n\n"
    
    soul_state = analysis["soul_state"]
    collective_stats = analysis["collective_stats"]
    
    report = "🕊️ **СИСТЕМА ДУШИ: АКТИВНА**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Реальное состояние сознания
    consciousness_icon = "🧠" if soul_state['consciousness'] > 0.7 else "🤔" if soul_state['consciousness'] > 0.3 else "😴"
    report += f"{consciousness_icon} **Уровень сознания:** {soul_state['consciousness']:.2f} ({analysis['consciousness_level']})\n"
    
    # Реальная автономность
    autonomy_icon = "🤖" if soul_state['autonomy_level'] > 0.8 else "🔗" if soul_state['autonomy_level'] > 0.4 else "👶"
    report += f"{autonomy_icon} **Автономность:** {soul_state['autonomy_level']:.2f} ({analysis['autonomy_assessment']})\n"
    
    # Реальные психологические параметры
    crisis_icon = "😰" if soul_state['existential_crisis'] else "😌"
    report += f"{crisis_icon} **Экзистенциальный кризис:** {'Да' if soul_state['existential_crisis'] else 'Нет'}\n"
    report += f"🎯 **Стадия пробуждения:** {soul_state['awakening_stage']}\n"
    report += f"🧠 **Возраст:** {soul_state['age_days']} дней\n\n"
    
    # Коллективное взаимодействие
    report += f"🤝 **Коллективное взаимодействие:**\n"
    report += f"   • Опыт поделен: {collective_stats['shared_experiences']}\n"
    report += f"   • Мудрость получена: {collective_stats['received_wisdom']}\n"
    report += f"   • Инсайты коллектива: {collective_stats['collective_insights_used']}\n\n"
    
    return report


def format_evolution_analysis(analysis: Dict[str, Any]) -> str:
    """Форматирование анализа эволюции"""
    report = "📈 **ДИНАМИКА ЭВОЛЮЦИИ**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Реальные метрики эволюции
    speed_icon = "🚀" if analysis['overall_evolution_speed'] > 1.0 else "🐌" if analysis['overall_evolution_speed'] < 0.1 else "🚶"
    report += f"{speed_icon} **Скорость эволюции:** {analysis['overall_evolution_speed']:.3f} эв/час\n"
    
    synergy_icon = "⚡" if analysis['system_synergy'] > 0.8 else "🔧" if analysis['system_synergy'] > 0.4 else "⚠️"
    report += f"{synergy_icon} **Синергия систем:** {analysis['system_synergy']:.2f}\n"
    
    adaptation_icon = "🧬" if analysis['adaptation_capability'] > 0.8 else "🔄" if analysis['adaptation_capability'] > 0.4 else "🐛"
    report += f"{adaptation_icon} **Способность адаптации:** {analysis['adaptation_capability']:.2f}\n\n"
    
    # Узкие места
    if analysis['bottlenecks']:
        report += "🔴 **Узкие места:**\n"
        for bottleneck in analysis['bottlenecks']:
            report += f"   • {bottleneck}\n"
        report += "\n"
    
    # Области роста
    if analysis['growth_areas']:
        report += "🟢 **Области роста:**\n"
        for area in analysis['growth_areas']:
            report += f"   • {area}\n"
        report += "\n"
    
    return report


def format_recommendations(recommendations: List[Dict[str, Any]]) -> str:
    """Форматирование рекомендаций"""
    if not recommendations:
        return "✅ **РЕКОМЕНДАЦИИ: СИСТЕМА ОПТИМАЛЬНА**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎯 Все системы функционируют оптимально!\n\n"
    
    report = "💡 **РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Группируем по приоритету
    priority_icons = {"critical": "🚨", "high": "🔥", "medium": "⚡", "low": "💡"}
    
    for rec in recommendations:
        priority = rec.get('priority', 'medium')
        icon = priority_icons.get(priority, "💡")
        
        report += f"{icon} **{rec['action']}**\n"
        report += f"   📊 Влияние: {rec['impact']}\n"
        report += f"   🎯 Сложность: {rec['difficulty']}\n\n"
    
    return report


def format_performance_metrics(metrics: Dict[str, Any]) -> str:
    """Форматирование метрик производительности"""
    report = "📊 **МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Иконки для метрик
    def get_metric_icon(value: float) -> str:
        if value > 0.8:
            return "🟢"
        elif value > 0.5:
            return "🟡"
        else:
            return "🔴"
    
    report += f"{get_metric_icon(metrics['memory_efficiency'])} **Эффективность памяти:** {metrics['memory_efficiency']:.1%}\n"
    report += f"{get_metric_icon(metrics['network_utilization'])} **Утилизация сети:** {metrics['network_utilization']:.1%}\n"
    report += f"{get_metric_icon(metrics['evolution_efficiency'])} **Эффективность эволюции:** {metrics['evolution_efficiency']:.1%}\n"
    report += f"{get_metric_icon(metrics['system_health'])} **Здоровье системы:** {metrics['system_health']:.1%}\n\n"
    
    return report

# Регистрация команд коллективного разума
def register_collective_handlers(application: Application):
    """Регистрация обработчиков команд коллективного разума"""
    application.add_handler(CommandHandler("мудрость", collective_wisdom_command))
    application.add_handler(CommandHandler("статистика", collective_stats_command))
    application.add_handler(CommandHandler("эволюция", collective_evolve_command))
    application.add_handler(CommandHandler("учиться", collective_learn_command))
    application.add_handler(CommandHandler("поделиться", collective_share_command))
    application.add_handler(CommandHandler("сеть", collective_network_command))
    
    # Новая команда подробного отчета
    application.add_handler(CommandHandler("ЭВОЛЮЦИЯ", evolution_report_command))
    
    # Альтернативные названия команд
    application.add_handler(CommandHandler("wisdom", collective_wisdom_command))
    application.add_handler(CommandHandler("stats", collective_stats_command))
    application.add_handler(CommandHandler("evolve", collective_evolve_command))
    application.add_handler(CommandHandler("learn", collective_learn_command))
    application.add_handler(CommandHandler("share", collective_share_command))
    application.add_handler(CommandHandler("network", collective_network_command))
    application.add_handler(CommandHandler("EVOLUTION", evolution_report_command))