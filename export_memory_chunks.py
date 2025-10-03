#!/usr/bin/env python3
"""
Экспорт чанков памяти бота по группам
Выгружает все знания бота о группах в текстовые файлы
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def export_memory_chunks():
    """Экспортирует все чанки памяти по группам"""
    
    # Путь к базе данных
    db_path = "data/smart_memory.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    print("🧠 ЭКСПОРТ ЧАНКОВ ПАМЯТИ БОТА")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем все группы
        cursor.execute("SELECT DISTINCT chat_id FROM memory_chunks")
        chat_ids = [row[0] for row in cursor.fetchall()]
        
        if not chat_ids:
            print("❌ Чанки памяти не найдены")
            return
        
        print(f"📊 Найдено групп с чанками: {len(chat_ids)}")
        
        # Создаем папку для экспорта
        export_dir = Path("exported_memory")
        export_dir.mkdir(exist_ok=True)
        
        total_chunks = 0
        
        for chat_id in chat_ids:
            print(f"\n📝 Обрабатываем группу: {chat_id}")
            
            # Получаем чанки для группы
            cursor.execute("""
                SELECT id, topic, content, created_at, source_period_start, source_period_end, relevance_base, message_count, participants
                FROM memory_chunks 
                WHERE chat_id = ?
                ORDER BY created_at ASC
            """, (chat_id,))
            
            chunks = cursor.fetchall()
            
            if not chunks:
                print(f"   ⚠️ Чанки не найдены для группы {chat_id}")
                continue
            
            print(f"   📦 Найдено чанков: {len(chunks)}")
            
            # Создаем файл для группы
            filename = f"group_{chat_id}_memory.txt"
            filepath = export_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"🧠 ПАМЯТЬ БОТА О ГРУППЕ {chat_id}\n")
                f.write(f"📅 Экспорт создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"📊 Всего чанков: {len(chunks)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, chunk in enumerate(chunks, 1):
                    chunk_id, topic, content, created_at, start_time, end_time, relevance, msg_count, participants = chunk
                    
                    # Конвертируем participants из JSON
                    try:
                        participants_list = json.loads(participants) if participants else []
                    except:
                        participants_list = []
                    
                    # Форматируем время
                    created_str = datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
                    start_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S') if start_time else "неизвестно"
                    end_str = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S') if end_time else "неизвестно"
                    
                    f.write(f"📦 ЧАНК #{i}\n")
                    f.write(f"🆔 ID: {chunk_id}\n")
                    f.write(f"📋 ТЕМА: {topic}\n")
                    f.write(f"📅 СОЗДАН: {created_str}\n")
                    f.write(f"⏰ ПЕРИОД: {start_str} - {end_str}\n")
                    f.write(f"⭐ РЕЛЕВАНТНОСТЬ: {relevance:.3f}\n")
                    f.write(f"💬 СООБЩЕНИЙ: {msg_count}\n")
                    f.write(f"👥 УЧАСТНИКИ: {', '.join(participants_list) if participants_list else 'неизвестно'}\n")
                    f.write(f"📝 СОДЕРЖАНИЕ:\n{content}\n")
                    f.write("-" * 80 + "\n\n")
            
            print(f"   ✅ Экспортировано в: {filepath}")
            total_chunks += len(chunks)
        
        # Создаем общий отчет
        report_file = export_dir / "memory_export_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("📊 ОТЧЕТ ОБ ЭКСПОРТЕ ПАМЯТИ БОТА\n")
            f.write("=" * 50 + "\n")
            f.write(f"📅 Дата экспорта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"📊 Всего групп: {len(chat_ids)}\n")
            f.write(f"📦 Всего чанков: {total_chunks}\n")
            f.write(f"📁 Папка экспорта: {export_dir.absolute()}\n\n")
            
            f.write("📋 СПИСОК ФАЙЛОВ:\n")
            for chat_id in chat_ids:
                f.write(f"- group_{chat_id}_memory.txt\n")
        
        conn.close()
        
        print(f"\n✅ ЭКСПОРТ ЗАВЕРШЕН!")
        print(f"📁 Папка: {export_dir.absolute()}")
        print(f"📊 Всего чанков: {total_chunks}")
        print(f"📋 Отчет: {report_file}")
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        import traceback
        traceback.print_exc()

def export_raw_messages():
    """Экспортирует сырые сообщения из групп"""
    
    db_path = "data/smart_memory.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    print("\n📝 ЭКСПОРТ СЫРЫХ СООБЩЕНИЙ")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем все группы
        cursor.execute("SELECT DISTINCT chat_id FROM group_messages")
        chat_ids = [row[0] for row in cursor.fetchall()]
        
        if not chat_ids:
            print("❌ Сообщения не найдены")
            return
        
        export_dir = Path("exported_memory")
        export_dir.mkdir(exist_ok=True)
        
        for chat_id in chat_ids:
            print(f"📝 Обрабатываем сообщения группы: {chat_id}")
            
            # Получаем сообщения
            cursor.execute("""
                SELECT user_id, content, timestamp, processed
                FROM group_messages 
                WHERE chat_id = ?
                ORDER BY timestamp ASC
            """, (chat_id,))
            
            messages = cursor.fetchall()
            
            if not messages:
                continue
            
            # Создаем файл
            filename = f"group_{chat_id}_raw_messages.txt"
            filepath = export_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"💬 СЫРЫЕ СООБЩЕНИЯ ГРУППЫ {chat_id}\n")
                f.write(f"📅 Экспорт: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"📊 Всего сообщений: {len(messages)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, msg in enumerate(messages, 1):
                    user_id, content, timestamp, processed = msg
                    time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    status = "✅ Обработано" if processed else "⏳ Не обработано"
                    
                    f.write(f"💬 СООБЩЕНИЕ #{i}\n")
                    f.write(f"👤 Пользователь: {user_id}\n")
                    f.write(f"⏰ Время: {time_str}\n")
                    f.write(f"📊 Статус: {status}\n")
                    f.write(f"📝 Текст:\n{content}\n")
                    f.write("-" * 80 + "\n\n")
            
            print(f"   ✅ Экспортировано {len(messages)} сообщений в: {filepath}")
        
        conn.close()
        print("✅ Экспорт сырых сообщений завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка экспорта сообщений: {e}")

if __name__ == "__main__":
    export_memory_chunks()
    export_raw_messages()
