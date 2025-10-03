#!/usr/bin/env python3
"""
Анализатор debug логов памяти - парсит logs/memory_debug.log
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter


class MemoryDebugAnalyzer:
    """Анализатор debug логов работы памяти"""
    
    def __init__(self, log_file: str = "logs/memory_debug.log"):
        self.log_file = log_file
        
    def parse_log_file(self) -> List[Dict[str, Any]]:
        """Парсит файл логов и извлекает все события памяти"""
        
        events = []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    event = self._parse_log_line(line.strip())
                    if event:
                        events.append(event)
        except FileNotFoundError:
            print(f"❌ Файл логов не найден: {self.log_file}")
            return []
        except Exception as e:
            print(f"❌ Ошибка чтения логов: {e}")
            return []
            
        return events
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Парсит одну строку лога"""
        
        # Шаблон для debug логов памяти
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?\| DEBUG\s+\| memory_debug\s+\| (\w+):(\d+)\s+\| (.+)'
        
        match = re.match(pattern, line)
        if not match:
            return None
            
        timestamp_str, function, line_num, message = match.groups()
        
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except:
            timestamp = None
            
        return {
            'timestamp': timestamp,
            'function': function,
            'line_number': int(line_num),
            'message': message,
            'raw_line': line
        }
    
    def analyze_memory_injection_sessions(self) -> Dict[str, Any]:
        """Анализирует сессии инжекции памяти"""
        
        events = self.parse_log_file()
        
        if not events:
            return {'error': 'Нет событий для анализа'}
        
        # Группируем события по сессиям (начинаются с log_memory_injector_start)
        sessions = []
        current_session = None
        
        for event in events:
            if event['function'] == 'log_memory_injector_start':
                if current_session:
                    sessions.append(current_session)
                current_session = {
                    'start_time': event['timestamp'],
                    'events': [event],
                    'chunks_selected': 0,
                    'memory_used': 0,
                    'keywords': [],
                    'wisdom_searches': [],
                    'relevance_scores': []
                }
            elif current_session:
                current_session['events'].append(event)
                
                # Извлекаем ключевую информацию
                if 'MEMORY CHUNKS | Selected:' in event['message']:
                    match = re.search(r'Selected: (\d+)/(\d+)', event['message'])
                    if match:
                        current_session['chunks_selected'] = int(match.group(1))
                        
                elif 'MEMORY INJECTION | Used' in event['message']:
                    match = re.search(r'Memory: (\d+) tokens', event['message'])
                    if match:
                        current_session['memory_used'] = int(match.group(1))
                        
                elif 'INJECTOR KEYWORDS' in event['message']:
                    # Извлекаем ключевые слова (это сложно из-за формата)
                    if 'Query:' in event['message']:
                        # Упрощенный парсинг ключевых слов
                        current_session['keywords'] = 'extracted'  # Заглушка
                        
                elif 'COLLECTIVE WISDOM | Search:' in event['message']:
                    match = re.search(r"Search: '([^']+)'", event['message'])
                    if match:
                        current_session['wisdom_searches'].append(match.group(1))
                        
                elif 'RELEVANCE | ✅' in event['message']:
                    match = re.search(r'(\d+\.\d+) \(threshold:', event['message'])
                    if match:
                        current_session['relevance_scores'].append(float(match.group(1)))
        
        # Добавляем последнюю сессию
        if current_session:
            sessions.append(current_session)
        
        # Статистика
        total_sessions = len(sessions)
        sessions_with_memory = len([s for s in sessions if s['chunks_selected'] > 0])
        avg_chunks = sum(s['chunks_selected'] for s in sessions) / total_sessions if total_sessions > 0 else 0
        avg_memory_tokens = sum(s['memory_used'] for s in sessions) / total_sessions if total_sessions > 0 else 0
        
        # Популярные поисковые запросы
        all_searches = []
        for session in sessions:
            all_searches.extend(session['wisdom_searches'])
        
        popular_searches = Counter(all_searches).most_common(10)
        
        # Распределение релевантности
        all_relevance = []
        for session in sessions:
            all_relevance.extend(session['relevance_scores'])
        
        relevance_stats = {
            'min': min(all_relevance) if all_relevance else 0,
            'max': max(all_relevance) if all_relevance else 0,
            'avg': sum(all_relevance) / len(all_relevance) if all_relevance else 0,
            'count': len(all_relevance)
        }
        
        return {
            'total_sessions': total_sessions,
            'sessions_with_memory': sessions_with_memory,
            'memory_usage_rate': sessions_with_memory / total_sessions * 100 if total_sessions > 0 else 0,
            'avg_chunks_per_session': avg_chunks,
            'avg_memory_tokens': avg_memory_tokens,
            'popular_searches': popular_searches,
            'relevance_stats': relevance_stats,
            'recent_sessions': sessions[-5:] if len(sessions) >= 5 else sessions  # Последние 5
        }
    
    def show_contradiction_analysis(self) -> Dict[str, Any]:
        """Анализирует противоречия в логах"""
        
        events = self.parse_log_file()
        
        contradiction_indicators = [
            "НЕ используй старые воспоминания",
            "НЕ используй память",
            "игнорируй память",
            "только текущий контекст"
        ]
        
        memory_injection_indicators = [
            "MEMORY INJECTION | Used",
            "chunks selected",
            "Memory: \\d+ tokens"
        ]
        
        contradictions = []
        
        for event in events:
            message = event['message']
            
            # Ищем признаки противоречий
            has_prohibition = any(indicator.lower() in message.lower() for indicator in contradiction_indicators)
            has_injection = any(re.search(indicator, message) for indicator in memory_injection_indicators)
            
            if has_prohibition or has_injection:
                contradictions.append({
                    'timestamp': event['timestamp'],
                    'type': 'prohibition' if has_prohibition else 'injection',
                    'message': message,
                    'function': event['function']
                })
        
        # Группируем по времени (в пределах 1 минуты)
        contradiction_pairs = []
        
        for i, event in enumerate(contradictions):
            if event['type'] == 'prohibition':
                # Ищем инжекции в течение следующих 30 секунд
                for j in range(i+1, len(contradictions)):
                    other = contradictions[j]
                    if other['type'] == 'injection':
                        time_diff = (other['timestamp'] - event['timestamp']).total_seconds()
                        if 0 <= time_diff <= 30:
                            contradiction_pairs.append({
                                'prohibition': event,
                                'injection': other,
                                'time_gap_seconds': time_diff
                            })
                            break
        
        return {
            'total_contradictions': len(contradiction_pairs),
            'contradictions': contradiction_pairs[-5:],  # Последние 5
            'prohibition_count': len([c for c in contradictions if c['type'] == 'prohibition']),
            'injection_count': len([c for c in contradictions if c['type'] == 'injection'])
        }
    
    def generate_report(self) -> str:
        """Генерирует отчет по анализу логов"""
        
        print("🔍 АНАЛИЗ DEBUG ЛОГОВ ПАМЯТИ")
        print("=" * 50)
        
        # Анализ сессий инжекции
        injection_analysis = self.analyze_memory_injection_sessions()
        
        if 'error' in injection_analysis:
            return f"❌ {injection_analysis['error']}"
        
        print(f"📊 СТАТИСТИКА ИНЖЕКЦИЙ:")
        print(f"  • Всего сессий: {injection_analysis['total_sessions']}")
        print(f"  • Сессий с памятью: {injection_analysis['sessions_with_memory']}")
        print(f"  • Процент использования памяти: {injection_analysis['memory_usage_rate']:.1f}%")
        print(f"  • Среднее чанков на сессию: {injection_analysis['avg_chunks_per_session']:.1f}")
        print(f"  • Среднее токенов памяти: {injection_analysis['avg_memory_tokens']:.0f}")
        
        print(f"\n🔎 ПОПУЛЯРНЫЕ ПОИСКОВЫЕ ЗАПРОСЫ:")
        for search, count in injection_analysis['popular_searches'][:5]:
            print(f"  • '{search}': {count} раз")
        
        relevance = injection_analysis['relevance_stats']
        print(f"\n📈 РЕЛЕВАНТНОСТЬ:")
        print(f"  • Минимальная: {relevance['min']:.3f}")
        print(f"  • Максимальная: {relevance['max']:.3f}")
        print(f"  • Средняя: {relevance['avg']:.3f}")
        print(f"  • Всего оценок: {relevance['count']}")
        
        # Анализ противоречий
        contradiction_analysis = self.show_contradiction_analysis()
        
        print(f"\n⚔️ АНАЛИЗ ПРОТИВОРЕЧИЙ:")
        print(f"  • Найдено противоречий: {contradiction_analysis['total_contradictions']}")
        print(f"  • Запретов на память: {contradiction_analysis['prohibition_count']}")
        print(f"  • Инжекций памяти: {contradiction_analysis['injection_count']}")
        
        if contradiction_analysis['contradictions']:
            print(f"\n🚨 ПОСЛЕДНИЕ ПРОТИВОРЕЧИЯ:")
            for i, contradiction in enumerate(contradiction_analysis['contradictions'], 1):
                prohibition = contradiction['prohibition']
                injection = contradiction['injection']
                gap = contradiction['time_gap_seconds']
                
                print(f"  {i}. Запрет в {prohibition['timestamp']} → Инжекция через {gap:.1f}с")
                print(f"     Запрет: {prohibition['message'][:100]}...")
                print(f"     Инжекция: {injection['message'][:100]}...")
        
        # Последние сессии
        print(f"\n📝 ПОСЛЕДНИЕ 3 СЕССИИ:")
        for i, session in enumerate(injection_analysis['recent_sessions'][-3:], 1):
            print(f"  {i}. {session['start_time']} | Чанков: {session['chunks_selected']} | "
                  f"Токенов: {session['memory_used']} | Поиски: {len(session['wisdom_searches'])}")
        
        return "✅ Анализ завершен"


def main():
    """Запуск анализатора"""
    
    analyzer = MemoryDebugAnalyzer()
    result = analyzer.generate_report()
    print(f"\n{result}")


if __name__ == "__main__":
    main()