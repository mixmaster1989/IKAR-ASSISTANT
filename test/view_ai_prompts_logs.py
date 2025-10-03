#!/usr/bin/env python3
"""
🧠 ПРОСМОТР ЛОГОВ ПРОМПТОВ AI МОДЕЛЕЙ
Интерактивный просмотр и анализ логов взаимодействия с AI моделями
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from collections import defaultdict, Counter

class AIPromptsLogViewer:
    """Просмотрщик логов промптов AI моделей"""
    
    def __init__(self, log_file: str = "ai_prompts.log"):
        self.log_file = Path(log_file)
        self.prompts_dir = self.log_file.parent / "prompts"
        self.responses_dir = self.log_file.parent / "responses"
        self.conversations_dir = self.log_file.parent / "conversations"
        
    def read_log_file(self, lines: int = None) -> List[str]:
        """Чтение файла логов"""
        if not self.log_file.exists():
            print(f"❌ Файл логов не найден: {self.log_file}")
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                if lines:
                    return f.readlines()[-lines:]
                else:
                    return f.readlines()
        except Exception as e:
            print(f"❌ Ошибка чтения файла логов: {e}")
            return []
    
    def parse_log_entry(self, line: str) -> Optional[Dict[str, Any]]:
        """Парсинг записи лога"""
        try:
            # Формат: timestamp | level | name | func:line | message
            parts = line.strip().split(' | ')
            if len(parts) < 5:
                return None
            
            timestamp_str = parts[0]
            level = parts[1]
            name = parts[2]
            func_line = parts[3]
            message = ' | '.join(parts[4:])
            
            # Парсим timestamp
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except:
                timestamp = None
            
            # Извлекаем тип операции из сообщения
            operation_type = "unknown"
            if "🧠 AI ЗАПРОС:" in message:
                operation_type = "prompt_request"
            elif "✅ AI ОТВЕТ:" in message or "❌ AI ОТВЕТ:" in message:
                operation_type = "prompt_response"
            elif "💬 AI БЕСЕДА:" in message:
                operation_type = "prompt_conversation"
            elif "🔬 AI АНАЛИЗ:" in message:
                operation_type = "prompt_analysis"
            elif "⚡ AI ПРОИЗВОДИТЕЛЬНОСТЬ:" in message:
                operation_type = "prompt_performance"
            elif "❌ AI ОШИБКА:" in message:
                operation_type = "prompt_error"
            elif "⚙️ КОНФИГУРАЦИЯ МОДЕЛИ:" in message:
                operation_type = "model_config"
            elif "📊 КАЧЕСТВО ПРОМПТА:" in message:
                operation_type = "prompt_quality"
            
            return {
                "timestamp": timestamp,
                "timestamp_str": timestamp_str,
                "level": level,
                "name": name,
                "func_line": func_line,
                "message": message,
                "operation_type": operation_type
            }
        except Exception as e:
            print(f"❌ Ошибка парсинга записи: {e}")
            return None
    
    def get_logs_by_type(self, operation_type: str = None, hours: int = None) -> List[Dict[str, Any]]:
        """Получение логов по типу операции"""
        lines = self.read_log_file()
        logs = []
        
        for line in lines:
            entry = self.parse_log_entry(line)
            if not entry:
                continue
            
            # Фильтр по типу операции
            if operation_type and entry["operation_type"] != operation_type:
                continue
            
            # Фильтр по времени
            if hours and entry["timestamp"]:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                if entry["timestamp"] < cutoff_time:
                    continue
            
            logs.append(entry)
        
        return logs
    
    def get_prompts_stats(self) -> Dict[str, Any]:
        """Получение статистики промптов"""
        try:
            from ai_prompts_logger import get_ai_prompts_logger
            logger = get_ai_prompts_logger()
            return logger.get_prompts_stats()
        except ImportError:
            return self._calculate_stats_manually()
    
    def _calculate_stats_manually(self) -> Dict[str, Any]:
        """Ручной расчет статистики"""
        logs = self.get_logs_by_type()
        
        stats = {
            "total_prompts": 0,
            "total_responses": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "models_used": set(),
            "average_processing_time": 0.0,
            "total_tokens": 0,
            "operation_types": Counter(),
            "errors": []
        }
        
        processing_times = []
        
        for log in logs:
            stats["operation_types"][log["operation_type"]] += 1
            
            if log["operation_type"] == "prompt_request":
                stats["total_prompts"] += 1
                
                # Извлекаем модель
                model_match = re.search(r'Модель: (.+)', log["message"])
                if model_match:
                    stats["models_used"].add(model_match.group(1))
            
            elif log["operation_type"] == "prompt_response":
                stats["total_responses"] += 1
                
                if "✅" in log["message"]:
                    stats["successful_responses"] += 1
                else:
                    stats["failed_responses"] += 1
                    # Извлекаем ошибку
                    error_match = re.search(r'Ошибка: (.+)', log["message"])
                    if error_match:
                        stats["errors"].append(error_match.group(1))
                
                # Извлекаем время обработки
                time_match = re.search(r'Время обработки: ([\d.]+)с', log["message"])
                if time_match:
                    processing_times.append(float(time_match.group(1)))
                
                # Извлекаем токены
                tokens_match = re.search(r'Токенов использовано: (\d+)', log["message"])
                if tokens_match:
                    stats["total_tokens"] += int(tokens_match.group(1))
        
        if processing_times:
            stats["average_processing_time"] = sum(processing_times) / len(processing_times)
        
        # Преобразуем set в list
        stats["models_used"] = list(stats["models_used"])
        
        return stats
    
    def show_summary(self):
        """Показать сводку логов"""
        print("📊 СВОДКА ЛОГОВ ПРОМПТОВ AI")
        print("=" * 50)
        
        stats = self.get_prompts_stats()
        
        print(f"📝 Всего промптов: {stats.get('total_prompts', 0)}")
        print(f"💬 Всего ответов: {stats.get('total_responses', 0)}")
        print(f"✅ Успешных ответов: {stats.get('successful_responses', 0)}")
        print(f"❌ Ошибок: {stats.get('failed_responses', 0)}")
        print(f"⚡ Среднее время обработки: {stats.get('average_processing_time', 0):.2f}с")
        print(f"🔢 Всего токенов: {stats.get('total_tokens', 0)}")
        
        if stats.get('models_used'):
            print(f"🤖 Использованные модели: {', '.join(stats['models_used'])}")
        
        print("\n📈 Типы операций:")
        for op_type, count in stats.get('operation_types', {}).most_common():
            print(f"   {op_type}: {count}")
        
        if stats.get('errors'):
            print(f"\n❌ Последние ошибки:")
            for error in stats['errors'][-5:]:
                print(f"   • {error}")
    
    def show_recent_prompts(self, count: int = 10):
        """Показать последние промпты"""
        print(f"🧠 ПОСЛЕДНИЕ {count} ПРОМПТОВ")
        print("=" * 50)
        
        logs = self.get_logs_by_type("prompt_request", hours=24)
        recent_logs = logs[-count:] if len(logs) > count else logs
        
        for i, log in enumerate(reversed(recent_logs), 1):
            print(f"\n{i}. {log['timestamp_str']}")
            
            # Извлекаем модель
            model_match = re.search(r'Модель: (.+)', log["message"])
            if model_match:
                print(f"   Модель: {model_match.group(1)}")
            
            # Извлекаем системный промпт
            system_prompt_match = re.search(r'Системный промпт:\s*\n\s*(.+)', log["message"], re.DOTALL)
            if system_prompt_match:
                system_prompt = system_prompt_match.group(1).strip()
                print(f"   📝 Системный промпт: {system_prompt[:200]}{'...' if len(system_prompt) > 200 else ''}")
            
            # Извлекаем пользовательский промпт
            user_prompt_match = re.search(r'Пользовательский промпт:\s*\n\s*(.+)', log["message"], re.DOTALL)
            if user_prompt_match:
                user_prompt = user_prompt_match.group(1).strip()
                print(f"   💬 Пользовательский промпт: {user_prompt[:200]}{'...' if len(user_prompt) > 200 else ''}")
            
            # Показываем полные промпты из JSON файлов если доступны
            request_id_match = re.search(r'AI ЗАПРОС: (.+)', log["message"])
            if request_id_match:
                request_id = request_id_match.group(1)
                self._show_full_prompt_from_file(request_id, show_full=False)
    
    def show_recent_responses(self, count: int = 10):
        """Показать последние ответы"""
        print(f"💬 ПОСЛЕДНИЕ {count} ОТВЕТОВ")
        print("=" * 50)
        
        logs = self.get_logs_by_type("prompt_response", hours=24)
        recent_logs = logs[-count:] if len(logs) > count else logs
        
        for i, log in enumerate(reversed(recent_logs), 1):
            print(f"\n{i}. {log['timestamp_str']}")
            
            # Статус
            if "✅" in log["message"]:
                print("   ✅ Успешно")
            else:
                print("   ❌ Ошибка")
            
            # Извлекаем модель
            model_match = re.search(r'Модель: (.+)', log["message"])
            if model_match:
                print(f"   Модель: {model_match.group(1)}")
            
            # Извлекаем время обработки
            time_match = re.search(r'Время обработки: ([\d.]+)с', log["message"])
            if time_match:
                print(f"   Время: {time_match.group(1)}с")
            
            # Извлекаем токены
            tokens_match = re.search(r'Токенов использовано: (\d+)', log["message"])
            if tokens_match:
                print(f"   Токены: {tokens_match.group(1)}")
            
            # Извлекаем ответ
            response_match = re.search(r'Ответ:\s*\n\s*(.+)', log["message"], re.DOTALL)
            if response_match:
                response = response_match.group(1).strip()
                print(f"   💬 Ответ: {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # Показываем полные ответы из JSON файлов если доступны
            request_id_match = re.search(r'AI ОТВЕТ: (.+)', log["message"])
            if request_id_match:
                request_id = request_id_match.group(1)
                self._show_full_response_from_file(request_id, show_full=False)
    
    def show_errors(self, count: int = 10):
        """Показать ошибки"""
        print(f"❌ ПОСЛЕДНИЕ {count} ОШИБОК")
        print("=" * 50)
        
        logs = self.get_logs_by_type("prompt_error", hours=24)
        recent_logs = logs[-count:] if len(logs) > count else logs
        
        for i, log in enumerate(reversed(recent_logs), 1):
            print(f"\n{i}. {log['timestamp_str']}")
            print(f"   {log['message']}")
    
    def show_performance(self, hours: int = 24):
        """Показать производительность"""
        print(f"⚡ ПРОИЗВОДИТЕЛЬНОСТЬ ЗА ПОСЛЕДНИЕ {hours} ЧАСОВ")
        print("=" * 50)
        
        logs = self.get_logs_by_type("prompt_performance", hours=hours)
        
        if not logs:
            print("Нет данных о производительности")
            return
        
        # Группируем по операциям
        operations = defaultdict(list)
        for log in logs:
            op_match = re.search(r'AI ПРОИЗВОДИТЕЛЬНОСТЬ: (.+)', log["message"])
            if op_match:
                operation = op_match.group(1)
                time_match = re.search(r'Время выполнения: ([\d.]+)с', log["message"])
                if time_match:
                    operations[operation].append(float(time_match.group(1)))
        
        for operation, times in operations.items():
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            print(f"\n{operation}:")
            print(f"   Среднее время: {avg_time:.2f}с")
            print(f"   Минимальное время: {min_time:.2f}с")
            print(f"   Максимальное время: {max_time:.2f}с")
            print(f"   Количество операций: {len(times)}")
    
    def search_logs(self, query: str, hours: int = 24):
        """Поиск в логах"""
        print(f"🔍 ПОИСК В ЛОГАХ: '{query}'")
        print("=" * 50)
        
        logs = self.get_logs_by_type(hours=hours)
        matching_logs = []
        
        for log in logs:
            if query.lower() in log["message"].lower():
                matching_logs.append(log)
        
        print(f"Найдено записей: {len(matching_logs)}")
        
        for i, log in enumerate(matching_logs[-10:], 1):
            print(f"\n{i}. {log['timestamp_str']} - {log['operation_type']}")
            print(f"   {log['message'][:200]}...")
    
    def _show_full_prompt_from_file(self, request_id: str, show_full: bool = True):
        """Показать полный промпт из JSON файла"""
        prompt_file = self.prompts_dir / f"{request_id}_prompt.json"
        
        if prompt_file.exists():
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                
                if show_full:
                    print(f"\n📄 ПОЛНЫЙ ПРОМПТ: {request_id}")
                    print("=" * 50)
                    print(f"🕐 Время: {prompt_data.get('timestamp', 'N/A')}")
                    print(f"🤖 Модель: {prompt_data.get('model', 'N/A')}")
                    print(f"\n📝 Системный промпт:")
                    print(prompt_data.get('system_prompt', 'N/A'))
                    print(f"\n💬 Пользовательский промпт:")
                    print(prompt_data.get('user_prompt', 'N/A'))
                    
                    if prompt_data.get('context'):
                        print(f"\n🔧 Контекст:")
                        print(json.dumps(prompt_data['context'], ensure_ascii=False, indent=2))
                else:
                    # Краткий вид
                    system_prompt = prompt_data.get('system_prompt', '')
                    user_prompt = prompt_data.get('user_prompt', '')
                    print(f"   📝 Системный: {system_prompt[:100]}{'...' if len(system_prompt) > 100 else ''}")
                    print(f"   💬 Пользовательский: {user_prompt[:100]}{'...' if len(user_prompt) > 100 else ''}")
                
            except Exception as e:
                print(f"   ❌ Ошибка чтения промпта: {e}")
        else:
            if show_full:
                print("❌ Файл промпта не найден")
    
    def _show_full_response_from_file(self, request_id: str, show_full: bool = True):
        """Показать полный ответ из JSON файла"""
        response_file = self.responses_dir / f"{request_id}_response.json"
        
        if response_file.exists():
            try:
                with open(response_file, 'r', encoding='utf-8') as f:
                    response_data = json.load(f)
                
                if show_full:
                    print(f"\n💬 ПОЛНЫЙ ОТВЕТ: {request_id}")
                    print("=" * 50)
                    print(f"🕐 Время: {response_data.get('timestamp', 'N/A')}")
                    print(f"✅ Успех: {response_data.get('success', 'N/A')}")
                    
                    if response_data.get('processing_time'):
                        print(f"⚡ Время обработки: {response_data['processing_time']:.2f}с")
                    
                    if response_data.get('tokens_used'):
                        print(f"🔢 Токенов: {response_data['tokens_used']}")
                    
                    if response_data.get('error'):
                        print(f"❌ Ошибка: {response_data['error']}")
                    
                    print(f"\n📄 Полный ответ:")
                    print(response_data.get('response', 'N/A'))
                else:
                    # Краткий вид
                    response = response_data.get('response', '')
                    print(f"   💬 Полный ответ: {response[:100]}{'...' if len(response) > 100 else ''}")
                
            except Exception as e:
                print(f"   ❌ Ошибка чтения ответа: {e}")
        else:
            if show_full:
                print("❌ Файл ответа не найден")
    
    def show_full_prompt(self, request_id: str):
        """Показать полный промпт и ответ"""
        print(f"📄 ПОЛНЫЙ ПРОМПТ И ОТВЕТ: {request_id}")
        print("=" * 50)
        
        # Показываем промпт
        self._show_full_prompt_from_file(request_id, show_full=True)
        
        # Показываем ответ
        self._show_full_response_from_file(request_id, show_full=True)

def main():
    parser = argparse.ArgumentParser(description="Просмотр логов промптов AI моделей")
    parser.add_argument("--log-file", default="ai_prompts.log", help="Путь к файлу логов")
    parser.add_argument("--action", choices=["summary", "prompts", "responses", "errors", "performance", "search", "full"], 
                       default="summary", help="Действие")
    parser.add_argument("--count", type=int, default=10, help="Количество записей")
    parser.add_argument("--hours", type=int, default=24, help="Количество часов для фильтрации")
    parser.add_argument("--query", help="Поисковый запрос")
    parser.add_argument("--request-id", help="ID запроса для полного просмотра")
    
    args = parser.parse_args()
    
    viewer = AIPromptsLogViewer(args.log_file)
    
    if args.action == "summary":
        viewer.show_summary()
    elif args.action == "prompts":
        viewer.show_recent_prompts(args.count)
    elif args.action == "responses":
        viewer.show_recent_responses(args.count)
    elif args.action == "errors":
        viewer.show_errors(args.count)
    elif args.action == "performance":
        viewer.show_performance(args.hours)
    elif args.action == "search":
        if not args.query:
            print("❌ Укажите поисковый запрос с --query")
            return
        viewer.search_logs(args.query, args.hours)
    elif args.action == "full":
        if not args.request_id:
            print("❌ Укажите ID запроса с --request-id")
            return
        viewer.show_full_prompt(args.request_id)

if __name__ == "__main__":
    main() 