#!/usr/bin/env python3
"""
🚀 Главный скрипт для анализа коллективного разума IKAR
Запускает все инструменты мониторинга и анализа
"""

import asyncio
import sys
import subprocess
from pathlib import Path
import argparse
from datetime import datetime, timedelta

def print_banner():
    """Вывод баннера"""
    print("🧬" + "="*60)
    print("🧬 IKAR COLLECTIVE MIND ANALYSIS TOOLS")
    print("🧬" + "="*60)
    print()

def check_dependencies():
    """Проверка зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pandas', 'matplotlib', 
        'seaborn', 'aiohttp', 'sqlite3'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        print("Установите их командой: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ Все зависимости установлены")
    return True

def check_database():
    """Проверка базы данных"""
    db_path = Path("data/collective_mind.db")
    
    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        print("Убедитесь, что система коллективного разума запущена")
        return False
    
    print(f"✅ База данных найдена: {db_path}")
    return True

async def run_comprehensive_analysis():
    """Запуск комплексного анализа"""
    print("📊 Запуск комплексного анализа...")
    
    try:
        # Импортируем анализатор
        from collective_agents_analyzer import CollectiveAgentsAnalyzer
        
        analyzer = CollectiveAgentsAnalyzer()
        analyzer._init_database()
        
        # Генерируем отчет
        report = await analyzer.generate_comprehensive_report()
        
        # Сохраняем отчет
        report_file = Path("reports/comprehensive_collective_report.txt")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📊 Комплексный отчет сохранен: {report_file}")
        
        # Генерируем визуальный отчет
        await analyzer.generate_visual_report()
        
        # Экспортируем данные
        await analyzer.export_agent_data()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка комплексного анализа: {e}")
        return False

async def run_live_monitor():
    """Запуск живого монитора"""
    print("🔍 Запуск живого монитора...")
    
    try:
        from collective_monitor import CollectiveMonitor
        
        monitor = CollectiveMonitor()
        
        # Генерируем живой отчет
        report = await monitor.generate_live_report()
        
        # Сохраняем отчет
        report_file = Path("reports/live_collective_report.txt")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📊 Живой отчет сохранен: {report_file}")
        
        # Запускаем терминальный монитор
        print("🔍 Запуск терминального монитора (Ctrl+C для остановки)...")
        monitor.run_terminal_monitor()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка живого монитора: {e}")
        return False

def run_web_dashboard():
    """Запуск веб-дашборда"""
    print("🌐 Запуск веб-дашборда...")
    
    try:
        # Запускаем веб-сервер в отдельном процессе
        process = subprocess.Popen([
            sys.executable, "collective_web_dashboard.py"
        ])
        
        print("🌐 Веб-дашборд запущен: http://localhost:8080")
        print("Нажмите Ctrl+C для остановки")
        
        try:
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
            print("\n🛑 Веб-дашборд остановлен")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка веб-дашборда: {e}")
        return False

def show_quick_report():
    """Показать быстрый отчет"""
    print("📋 Быстрый отчет по коллективному разуму")
    print("-" * 50)
    
    try:
        import sqlite3
        from datetime import datetime
        
        db_path = Path("data/collective_mind.db")
        
        if not db_path.exists():
            print("❌ База данных не найдена")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(DISTINCT agent_id) FROM collective_memories")
        total_agents = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM collective_memories")
        total_memories = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM evolution_events")
        total_evolution = cursor.fetchone()[0] or 0
        
        # Активность за последние 24 часа
        day_ago = (datetime.now() - timedelta(days=1)).timestamp()
        cursor.execute("""
            SELECT COUNT(DISTINCT agent_id) 
            FROM collective_memories 
            WHERE timestamp > ?
        """, (day_ago,))
        active_agents = cursor.fetchone()[0] or 0
        
        # Топ агентов
        cursor.execute("""
            SELECT agent_id, COUNT(*) as count
            FROM collective_memories
            GROUP BY agent_id
            ORDER BY count DESC
            LIMIT 3
        """)
        top_agents = cursor.fetchall()
        
        conn.close()
        
        print(f"🤖 Всего агентов: {total_agents}")
        print(f"🧠 Общих воспоминаний: {total_memories}")
        print(f"🔄 Событий эволюции: {total_evolution}")
        print(f"⚡ Активных за 24ч: {active_agents}")
        print()
        
        print("🏆 Топ-3 агента по активности:")
        for i, (agent_id, count) in enumerate(top_agents, 1):
            print(f"  {i}. {agent_id[:16]}... - {count} воспоминаний")
        
    except Exception as e:
        print(f"❌ Ошибка быстрого отчета: {e}")

async def main():
    """Основная функция"""
    print_banner()
    
    parser = argparse.ArgumentParser(description='Инструменты анализа коллективного разума IKAR')
    parser.add_argument('--mode', choices=['comprehensive', 'live', 'web', 'quick'], 
                       default='quick', help='Режим работы')
    parser.add_argument('--check-only', action='store_true', 
                       help='Только проверка системы')
    
    args = parser.parse_args()
    
    # Проверка зависимостей
    if not check_dependencies():
        return
    
    # Проверка базы данных
    if not check_database():
        return
    
    if args.check_only:
        print("✅ Система готова к работе")
        return
    
    # Запуск выбранного режима
    if args.mode == 'comprehensive':
        print("📊 Режим: Комплексный анализ")
        success = await run_comprehensive_analysis()
        if success:
            print("✅ Комплексный анализ завершен")
        else:
            print("❌ Ошибка комплексного анализа")
    
    elif args.mode == 'live':
        print("🔍 Режим: Живой монитор")
        success = await run_live_monitor()
        if success:
            print("✅ Живой монитор завершен")
        else:
            print("❌ Ошибка живого монитора")
    
    elif args.mode == 'web':
        print("🌐 Режим: Веб-дашборд")
        success = run_web_dashboard()
        if success:
            print("✅ Веб-дашборд завершен")
        else:
            print("❌ Ошибка веб-дашборда")
    
    elif args.mode == 'quick':
        print("📋 Режим: Быстрый отчет")
        show_quick_report()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Работа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}") 