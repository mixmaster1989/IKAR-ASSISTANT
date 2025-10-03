#!/usr/bin/env python3
"""
Инструменты мониторинга и анализа работы памяти бота
"""

import time
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import sys
import os

# Добавляем путь к backend для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory_injector import get_memory_injector
from core.collective_mind import CollectiveMind
from config import Config


class MemoryMonitor:
    """Монитор работы системы памяти"""
    
    def __init__(self):
        self.config = Config()
        self.memory_injector = get_memory_injector()
        self.collective_mind = CollectiveMind(self.config)
        
    async def analyze_prompt_injection(self, prompt: str, context: str = "", user_id: str = None) -> Dict[str, Any]:
        """Детальный анализ того что будет инжектировано для промпта"""
        
        print(f"\n🔍 АНАЛИЗ ИНЖЕКЦИИ ПАМЯТИ")
        print(f"📝 Промпт: {prompt[:100]}...")
        print(f"👤 User ID: {user_id}")
        print(f"📄 Контекст: {context[:50]}..." if context else "📄 Контекст: отсутствует")
        
        # Анализируем что будет инжектировано
        memory_analysis = await self.memory_injector.analyze_memory_usage(prompt)
        
        print(f"\n📊 АНАЛИЗ ПОТЕНЦИАЛА ПАМЯТИ:")
        print(f"  • Всего доступно: {memory_analysis.get('total_available', 0)} чанков")
        print(f"  • Топ релевантность: {memory_analysis.get('top_relevance', 0):.3f}")
        print(f"  • Эффективность памяти: {memory_analysis.get('memory_efficiency', 0):.1%}")
        
        if memory_analysis.get('total_available', 0) > 0:
            # Делаем инжекцию и смотрим что получилось
            enhanced_prompt = await self.memory_injector.inject_memory_into_prompt(
                prompt, context, user_id, memory_budget=3000
            )
            
            print(f"\n💉 РЕЗУЛЬТАТ ИНЖЕКЦИИ:")
            original_tokens = len(prompt.split())
            enhanced_tokens = len(enhanced_prompt.split())
            memory_tokens = enhanced_tokens - original_tokens
            
            print(f"  • Оригинальный промпт: {original_tokens} токенов")
            print(f"  • Улучшенный промпт: {enhanced_tokens} токенов")
            print(f"  • Добавлено памяти: {memory_tokens} токенов")
            print(f"  • Процент памяти: {memory_tokens/enhanced_tokens*100:.1f}%")
            
            return {
                'analysis': memory_analysis,
                'original_prompt': prompt,
                'enhanced_prompt': enhanced_prompt,
                'token_stats': {
                    'original': original_tokens,
                    'enhanced': enhanced_tokens,
                    'memory_added': memory_tokens,
                    'memory_percentage': memory_tokens/enhanced_tokens*100
                }
            }
        else:
            print(f"\n❌ ПАМЯТЬ НЕ ИНЖЕКТИРОВАНА - нет релевантных чанков")
            return {
                'analysis': memory_analysis,
                'original_prompt': prompt,
                'enhanced_prompt': prompt,
                'token_stats': {'original': len(prompt.split()), 'enhanced': len(prompt.split()), 'memory_added': 0}
            }
    
    async def show_collective_memory_stats(self) -> Dict[str, Any]:
        """Показать статистику коллективной памяти"""
        
        print(f"\n🧠 СТАТИСТИКА КОЛЛЕКТИВНОЙ ПАМЯТИ")
        
        db_path = "data/collective_mind.db"
        if not os.path.exists(db_path):
            print(f"❌ База коллективной памяти не найдена: {db_path}")
            return {}
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*), memory_type FROM collective_memories GROUP BY memory_type")
        type_stats = cursor.fetchall()
        
        print(f"📈 По типам памяти:")
        total_memories = 0
        for count, mem_type in type_stats:
            print(f"  • {mem_type}: {count} записей")
            total_memories += count
            
        print(f"📊 Всего записей: {total_memories}")
        
        # Временная статистика
        current_time = time.time()
        day_ago = current_time - (24 * 60 * 60)
        week_ago = current_time - (7 * 24 * 60 * 60)
        month_ago = current_time - (30 * 24 * 60 * 60)
        
        cursor.execute("SELECT COUNT(*) FROM collective_memories WHERE timestamp > ?", (day_ago,))
        day_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM collective_memories WHERE timestamp > ?", (week_ago,))
        week_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM collective_memories WHERE timestamp > ?", (month_ago,))
        month_count = cursor.fetchone()[0]
        
        print(f"📅 По времени:")
        print(f"  • За последний день: {day_count}")
        print(f"  • За последнюю неделю: {week_count}")
        print(f"  • За последний месяц: {month_count}")
        print(f"  • Старше месяца: {total_memories - month_count}")
        
        # Самые релевантные записи для слова "бот"
        print(f"\n🔍 ТОП-5 записей для слова 'бот':")
        cursor.execute("""
            SELECT SUBSTR(content, 1, 100), importance, datetime(timestamp, 'unixepoch')
            FROM collective_memories 
            WHERE content LIKE '%бот%' 
            ORDER BY importance DESC 
            LIMIT 5
        """)
        
        bot_memories = cursor.fetchall()
        for i, (content, importance, timestamp) in enumerate(bot_memories, 1):
            print(f"  {i}. [{importance:.2f}] {content}... ({timestamp})")
        
        conn.close()
        
        return {
            'total_memories': total_memories,
            'by_type': dict(type_stats),
            'by_time': {
                'day': day_count,
                'week': week_count, 
                'month': month_count,
                'older': total_memories - month_count
            }
        }
    
    async def test_keyword_search(self, keyword: str, limit: int = 5) -> List[Dict]:
        """Тестирует поиск по ключевому слову в коллективной памяти"""
        
        print(f"\n🔎 ТЕСТ ПОИСКА: '{keyword}'")
        
        memories = await self.collective_mind.get_collective_wisdom(keyword, limit=limit)
        
        print(f"📋 Найдено: {len(memories)} записей")
        
        results = []
        for i, memory in enumerate(memories, 1):
            age_days = (time.time() - memory.timestamp) / (24 * 60 * 60)
            content_preview = memory.content[:100].replace('\n', ' ')
            
            print(f"  {i}. [{memory.importance:.2f}] {content_preview}...")
            print(f"     Возраст: {age_days:.1f} дней, Верификаций: {memory.verification_count}")
            
            results.append({
                'content': memory.content,
                'importance': memory.importance,
                'age_days': age_days,
                'verification_count': memory.verification_count
            })
        
        return results
    
    async def analyze_contradiction_potential(self, prompt: str) -> Dict[str, Any]:
        """Анализирует потенциал противоречий между промптом и памятью"""
        
        print(f"\n⚔️ АНАЛИЗ ПРОТИВОРЕЧИЙ")
        
        # Ключевые слова запрета в промпте
        prohibition_keywords = [
            "не используй", "не вспоминай", "не ссылайся", "игнорируй память",
            "только текущий", "без воспоминаний", "забудь", "не помни"
        ]
        
        # Инструкции использования памяти
        memory_keywords = [
            "вспомни", "помнишь", "используй память", "что знаешь",
            "из опыта", "ранее", "прошлый раз"
        ]
        
        prompt_lower = prompt.lower()
        
        prohibitions = [kw for kw in prohibition_keywords if kw in prompt_lower]
        memory_requests = [kw for kw in memory_keywords if kw in prompt_lower]
        
        print(f"🚫 Найдены запреты на память: {prohibitions}")
        print(f"💭 Найдены запросы памяти: {memory_requests}")
        
        # Проверяем будет ли инжектирована память
        analysis = await self.memory_injector.analyze_memory_usage(prompt)
        memory_will_inject = analysis.get('total_available', 0) > 0
        
        print(f"💉 Память будет инжектирована: {'ДА' if memory_will_inject else 'НЕТ'}")
        
        # Определяем уровень противоречия
        contradiction_level = "НИЗКИЙ"
        if prohibitions and memory_will_inject:
            contradiction_level = "ВЫСОКИЙ" if len(prohibitions) > 1 else "СРЕДНИЙ"
        elif memory_requests and not memory_will_inject:
            contradiction_level = "СРЕДНИЙ"
            
        print(f"⚠️ Уровень противоречий: {contradiction_level}")
        
        return {
            'prohibitions': prohibitions,
            'memory_requests': memory_requests,
            'memory_will_inject': memory_will_inject,
            'contradiction_level': contradiction_level,
            'memory_analysis': analysis
        }


async def main():
    """Интерактивный мониторинг памяти"""
    
    monitor = MemoryMonitor()
    
    print("🔧 МОНИТОР ПАМЯТИ БОТА")
    print("=" * 50)
    
    while True:
        print(f"\nВыберите действие:")
        print(f"1. Проанализировать инжекцию для промпта")
        print(f"2. Показать статистику коллективной памяти") 
        print(f"3. Тестировать поиск по ключевому слову")
        print(f"4. Анализ противоречий в промпте")
        print(f"0. Выход")
        
        choice = input(f"\nВведите номер: ").strip()
        
        try:
            if choice == "1":
                prompt = input("Введите промпт для анализа: ").strip()
                context = input("Введите контекст (необязательно): ").strip()
                user_id = input("Введите user_id (необязательно): ").strip()
                
                await monitor.analyze_prompt_injection(
                    prompt, 
                    context if context else "", 
                    user_id if user_id else None
                )
                
            elif choice == "2":
                await monitor.show_collective_memory_stats()
                
            elif choice == "3":
                keyword = input("Введите ключевое слово: ").strip()
                limit = input("Лимит результатов (по умолчанию 5): ").strip()
                limit = int(limit) if limit else 5
                
                await monitor.test_keyword_search(keyword, limit)
                
            elif choice == "4":
                prompt = input("Введите промпт для анализа противоречий: ").strip()
                await monitor.analyze_contradiction_potential(prompt)
                
            elif choice == "0":
                print("👋 До свидания!")
                break
                
            else:
                print("❌ Неверный выбор!")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    asyncio.run(main())