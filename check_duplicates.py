#!/usr/bin/env python3
"""
Скрипт для проверки дубликатов в базе данных
"""

import sqlite3
from collections import Counter

def check_duplicates():
    db_path = "data/chatumba.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем дубликаты в group_history
        cursor.execute("""
            SELECT chat_id, user_id, content, timestamp, COUNT(*) as count
            FROM group_history 
            WHERE content IS NOT NULL 
            AND content != ''
            AND content != '[photo]'
            AND content != '[voice]'
            GROUP BY chat_id, user_id, content, timestamp
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        
        duplicates = cursor.fetchall()
        
        print(f"🔍 Найдено {len(duplicates)} групп дубликатов:")
        for dup in duplicates:
            print(f"  - Чат: {dup[0]}, Пользователь: {dup[1]}, Дубликатов: {dup[4]}")
            print(f"    Контент: {dup[2][:50]}...")
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM group_history")
        total = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT DISTINCT chat_id, user_id, content, timestamp
                FROM group_history 
                WHERE content IS NOT NULL 
                AND content != ''
                AND content != '[photo]'
                AND content != '[voice]'
            )
        """)
        unique = cursor.fetchone()[0]
        
        print(f"\n📊 Статистика:")
        print(f"  - Всего записей: {total}")
        print(f"  - Уникальных записей: {unique}")
        print(f"  - Дубликатов: {total - unique}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_duplicates()