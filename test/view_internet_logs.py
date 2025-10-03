#!/usr/bin/env python3
"""
📊 ПРОСМОТР ЛОГОВ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА
Удобный просмотр и анализ логов для дебага
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import re
import json
from typing import List, Dict, Any, Optional

def read_log_file(log_file: str = "internet_intelligence.log") -> List[str]:
    """Чтение файла логов"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.readlines()
    except FileNotFoundError:
        print(f"❌ Файл логов {log_file} не найден")
        return []
    except Exception as e:
        print(f"❌ Ошибка чтения файла логов: {e}")
        return []

def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Парсинг строки лога"""
    try:
        # Формат: 2024-01-01 12:00:00 | INFO | internet_intelligence | function:123 | Сообщение
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+) \| (\w+) \| ([^|]+) \| (.+)'
        match = re.match(pattern, line.strip())
        
        if match:
            timestamp, level, logger_name, location, message = match.groups()
            return {
                'timestamp': timestamp,
                'level': level,
                'logger_name': logger_name,
                'location': location,
                'message': message,
                'raw_line': line.strip()
            }
        return None
    except Exception as e:
        print(f"❌ Ошибка парсинга строки: {e}")
        return None

def filter_logs_by_type(logs: List[Dict[str, Any]], log_type: str = None) -> List[Dict[str, Any]]:
    """Фильтрация логов по типу"""
    if not log_type:
        return logs
    
    filtered = []
    for log in logs:
        message = log.get('message', '')
        if log_type.lower() in message.lower():
            filtered.append(log)
    
    return filtered

def filter_logs_by_time(logs: List[Dict[str, Any]], hours: int = 24) -> List[Dict[str, Any]]:
    """Фильтрация логов по времени"""
    if hours <= 0:
        return logs
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    filtered = []
    
    for log in logs:
        try:
            log_time = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S')
            if log_time >= cutoff_time:
                filtered.append(log)
        except:
            continue
    
    return filtered

def analyze_logs(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Анализ логов"""
    analysis = {
        'total_entries': len(logs),
        'error_count': 0,
        'warning_count': 0,
        'info_count': 0,
        'debug_count': 0,
        'operations': {},
        'errors': [],
        'performance': [],
        'search_requests': [],
        'telegram_integrations': []
    }
    
    for log in logs:
        level = log.get('level', '')
        message = log.get('message', '')
        
        # Подсчет уровней
        if level == 'ERROR':
            analysis['error_count'] += 1
            analysis['errors'].append(log)
        elif level == 'WARNING':
            analysis['warning_count'] += 1
        elif level == 'INFO':
            analysis['info_count'] += 1
        elif level == 'DEBUG':
            analysis['debug_count'] += 1
        
        # Анализ операций
        if '🔍 ПОИСКОВЫЙ ЗАПРОС' in message:
            analysis['search_requests'].append(log)
        elif '📱 TELEGRAM ИНТЕГРАЦИЯ' in message:
            analysis['telegram_integrations'].append(log)
        elif '⚡ ПРОИЗВОДИТЕЛЬНОСТЬ' in message:
            analysis['performance'].append(log)
        
        # Подсчет типов операций
        for operation in ['ПОИСК', 'ИЗВЛЕЧЕНИЕ', 'AI-ОБРАБОТКА', 'УЛУЧШЕНИЕ', 'ОШИБКА']:
            if operation in message:
                analysis['operations'][operation] = analysis['operations'].get(operation, 0) + 1
    
    return analysis

def print_log_summary(analysis: Dict[str, Any]):
    """Вывод сводки логов"""
    print("📊 СВОДКА ЛОГОВ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА")
    print("=" * 60)
    print(f"📈 Всего записей: {analysis['total_entries']}")
    print(f"✅ INFO: {analysis['info_count']}")
    print(f"⚠️  WARNING: {analysis['warning_count']}")
    print(f"❌ ERROR: {analysis['error_count']}")
    print(f"🔧 DEBUG: {analysis['debug_count']}")
    
    print(f"\n🔍 Поисковых запросов: {len(analysis['search_requests'])}")
    print(f"📱 Telegram интеграций: {len(analysis['telegram_integrations'])}")
    print(f"⚡ Записей производительности: {len(analysis['performance'])}")
    
    if analysis['operations']:
        print(f"\n📋 ОПЕРАЦИИ:")
        for operation, count in analysis['operations'].items():
            print(f"   {operation}: {count}")
    
    if analysis['errors']:
        print(f"\n❌ ПОСЛЕДНИЕ ОШИБКИ:")
        for error in analysis['errors'][-5:]:  # Последние 5 ошибок
            print(f"   {error['timestamp']}: {error['message'][:100]}...")

def print_recent_logs(logs: List[Dict[str, Any]], count: int = 20):
    """Вывод последних логов"""
    print(f"\n📝 ПОСЛЕДНИЕ {count} ЗАПИСЕЙ:")
    print("=" * 60)
    
    for log in logs[-count:]:
        timestamp = log['timestamp']
        level = log['level']
        message = log['message']
        
        # Цветовая индикация уровней
        level_emoji = {
            'ERROR': '❌',
            'WARNING': '⚠️',
            'INFO': 'ℹ️',
            'DEBUG': '🔧'
        }.get(level, '📝')
        
        print(f"{level_emoji} {timestamp} | {message}")

def print_search_requests(logs: List[Dict[str, Any]]):
    """Вывод поисковых запросов"""
    print(f"\n🔍 ПОИСКОВЫЕ ЗАПРОСЫ:")
    print("=" * 60)
    
    for log in logs:
        message = log['message']
        if '🔍 ПОИСКОВЫЙ ЗАПРОС' in message:
            timestamp = log['timestamp']
            print(f"⏰ {timestamp}")
            
            # Извлекаем детали запроса
            lines = message.split('\n')
            for line in lines:
                if line.strip().startswith('   Запрос:'):
                    query = line.replace('   Запрос:', '').strip().strip("'")
                    print(f"   🔍 {query}")
                elif line.strip().startswith('   Пользователь:'):
                    user = line.replace('   Пользователь:', '').strip()
                    print(f"   👤 {user}")
                elif line.strip().startswith('   Чат:'):
                    chat = line.replace('   Чат:', '').strip()
                    print(f"   💬 {chat}")
            print()

def print_performance_logs(logs: List[Dict[str, Any]]):
    """Вывод логов производительности"""
    print(f"\n⚡ ПРОИЗВОДИТЕЛЬНОСТЬ:")
    print("=" * 60)
    
    for log in logs:
        message = log['message']
        if '⚡ ПРОИЗВОДИТЕЛЬНОСТЬ' in message:
            timestamp = log['timestamp']
            print(f"⏰ {timestamp}")
            
            lines = message.split('\n')
            for line in lines:
                if line.strip().startswith('   Время выполнения:'):
                    duration = line.replace('   Время выполнения:', '').strip()
                    print(f"   ⏱️  {duration}")
                elif line.strip().startswith('   '):
                    detail = line.strip()
                    print(f"   📊 {detail}")
            print()

def print_errors(logs: List[Dict[str, Any]], count: int = 10):
    """Вывод ошибок"""
    print(f"\n❌ ПОСЛЕДНИЕ {count} ОШИБОК:")
    print("=" * 60)
    
    for log in logs[-count:]:
        timestamp = log['timestamp']
        message = log['message']
        location = log['location']
        
        print(f"⏰ {timestamp}")
        print(f"📍 {location}")
        print(f"❌ {message}")
        print()

def interactive_menu():
    """Интерактивное меню"""
    while True:
        print("\n🎮 МЕНЮ ПРОСМОТРА ЛОГОВ")
        print("=" * 40)
        print("1. 📊 Общая сводка")
        print("2. 📝 Последние записи (20)")
        print("3. 🔍 Поисковые запросы")
        print("4. ⚡ Производительность")
        print("5. ❌ Ошибки")
        print("6. 🔍 Фильтр по типу")
        print("7. ⏰ Фильтр по времени")
        print("8. 📁 Изменить файл логов")
        print("0. ❌ Выход")
        print("-" * 40)
        
        choice = input("Выберите опцию: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            logs = read_log_file()
            parsed_logs = [parse_log_line(line) for line in logs if parse_log_line(line)]
            analysis = analyze_logs(parsed_logs)
            print_log_summary(analysis)
        elif choice == "2":
            logs = read_log_file()
            parsed_logs = [parse_log_line(line) for line in logs if parse_log_line(line)]
            print_recent_logs(parsed_logs)
        elif choice == "3":
            logs = read_log_file()
            parsed_logs = [parse_log_line(line) for line in logs if parse_log_line(line)]
            print_search_requests(parsed_logs)
        elif choice == "4":
            logs = read_log_file()
            parsed_logs = [parse_log_line(line) for line in logs if parse_log_line(line)]
            print_performance_logs(parsed_logs)
        elif choice == "5":
            logs = read_log_file()
            parsed_logs = [parse_log_line(line) for line in logs if parse_log_line(line)]
            errors = [log for log in parsed_logs if log.get('level') == 'ERROR']
            print_errors(errors)
        elif choice == "6":
            log_type = input("Введите тип для фильтрации (например, ПОИСК, ОШИБКА): ").strip()
            logs = read_log_file()
            parsed_logs = [parse_log_line(line) for line in logs if parse_log_line(line)]
            filtered_logs = filter_logs_by_type(parsed_logs, log_type)
            print_recent_logs(filtered_logs, len(filtered_logs))
        elif choice == "7":
            try:
                hours = int(input("Введите количество часов для фильтрации: ").strip())
                logs = read_log_file()
                parsed_logs = [parse_log_line(line) for line in logs if parse_log_line(line)]
                filtered_logs = filter_logs_by_time(parsed_logs, hours)
                print_recent_logs(filtered_logs, len(filtered_logs))
            except ValueError:
                print("❌ Неверный формат числа")
        elif choice == "8":
            new_file = input("Введите путь к файлу логов: ").strip()
            if os.path.exists(new_file):
                global current_log_file
                current_log_file = new_file
                print(f"✅ Файл логов изменен на: {new_file}")
            else:
                print("❌ Файл не найден")
        else:
            print("❌ Неверный выбор")

def main():
    """Главная функция"""
    print("🌐 ПРОСМОТР ЛОГОВ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА")
    print("=" * 60)
    
    # Проверяем наличие файла логов
    log_file = "internet_intelligence.log"
    if not os.path.exists(log_file):
        print(f"❌ Файл логов {log_file} не найден")
        print("💡 Убедитесь, что система интернет-интеллекта была запущена")
        return
    
    # Показываем информацию о файле
    file_size = os.path.getsize(log_file)
    file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
    
    print(f"📁 Файл: {log_file}")
    print(f"📊 Размер: {file_size:,} байт")
    print(f"⏰ Последнее изменение: {file_mtime}")
    
    # Быстрая сводка
    logs = read_log_file(log_file)
    if logs:
        parsed_logs = [parse_log_line(line) for line in logs if parse_log_line(line)]
        analysis = analyze_logs(parsed_logs)
        print_log_summary(analysis)
        
        # Интерактивное меню
        interactive_menu()
    else:
        print("❌ Файл логов пуст или поврежден")

if __name__ == "__main__":
    main() 