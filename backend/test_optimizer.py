#!/usr/bin/env python3
"""
Тестовый скрипт для оптимизатора памяти
"""
import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.memory_optimizer import create_memory_optimizer
from llm import OpenRouterClient
from config import Config

async def test_optimizer():
    """Тестирует оптимизатор памяти"""
    try:
        print("🔧 Инициализация...")
        config = Config()
        llm_client = OpenRouterClient(config)
        
        print("🚀 Создание оптимизатора...")
        optimizer = create_memory_optimizer('data/chatumba.db', llm_client)
        
        print("🔍 Проверяем чанки...")
        
        # Проверяем базу напрямую
        import sqlite3
        conn = sqlite3.connect('data/chatumba.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM group_history")
        count = cursor.fetchone()[0]
        print(f"📊 Записей в group_history: {count}")
        
        cursor.execute("SELECT chat_id, content, timestamp FROM group_history")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  Запись: {row}")
        conn.close()
        
        chunks = await optimizer.get_memory_chunks(limit=5)
        print(f"📊 Найдено чанков: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"  Чанк {i+1}: {chunk['source']} - {chunk['tokens']} токенов")
        
        print("🧠 Запуск цикла оптимизации...")
        try:
            await optimizer.optimize_memory_cycle()
        except Exception as e:
            print(f"❌ Ошибка в цикле оптимизации: {e}")
            import traceback
            traceback.print_exc()
        
        print("✅ Тест завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_optimizer()) 