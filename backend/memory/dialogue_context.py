"""
💬 Dialogue Context - Система хранения контекста диалогов с ботом
Позволяет боту помнить предыдущие обмены сообщениями для нативного общения
"""

import sqlite3
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("chatumba.dialogue_context")

@dataclass
class DialogueTurn:
    """Один ход в диалоге"""
    id: int
    chat_id: str
    user_id: str
    user_message: str
    bot_response: str
    timestamp: float
    message_id: int  # ID сообщения бота в Telegram
    is_quote: bool = False  # Является ли ответом на цитирование

class DialogueContextManager:
    """Менеджер контекста диалогов"""
    
    def __init__(self, db_path: str = "data/smart_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных для диалогов"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица диалогов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dialogue_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    message_id INTEGER NOT NULL,
                    is_quote BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для быстрого поиска
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dialogue_chat_time ON dialogue_context(chat_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dialogue_message_id ON dialogue_context(message_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dialogue_user ON dialogue_context(chat_id, user_id, timestamp)")
            
            conn.commit()
            conn.close()
            
            logger.info("✅ База данных диалогов инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы диалогов: {e}")
            raise
    
    def save_dialogue_turn(self, chat_id: str, user_id: str, user_message: str, 
                          bot_response: str, message_id: int, is_quote: bool = False) -> bool:
        """Сохраняет один ход диалога"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO dialogue_context 
                (chat_id, user_id, user_message, bot_response, timestamp, message_id, is_quote)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chat_id, user_id, user_message, bot_response, time.time(), message_id, is_quote))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"💾 Сохранен диалог для чата {chat_id}, пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения диалога: {e}")
            return False
    
    def get_recent_dialogue_context(self, chat_id: str, user_id: str, 
                                   limit: int = 5) -> List[DialogueTurn]:
        """Получает последние ходы диалога для контекста"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, chat_id, user_id, user_message, bot_response, 
                       timestamp, message_id, is_quote
                FROM dialogue_context
                WHERE chat_id = ? AND user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (chat_id, user_id, limit))
            
            turns = []
            for row in cursor.fetchall():
                turn = DialogueTurn(
                    id=row[0],
                    chat_id=row[1],
                    user_id=row[2],
                    user_message=row[3],
                    bot_response=row[4],
                    timestamp=row[5],
                    message_id=row[6],
                    is_quote=bool(row[7])
                )
                turns.append(turn)
            
            conn.close()
            
            # Возвращаем в хронологическом порядке (старые первыми)
            return list(reversed(turns))
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста диалога: {e}")
            return []
    
    def find_bot_message_by_id(self, message_id: int) -> Optional[DialogueTurn]:
        """Находит сообщение бота по ID для цитирования"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, chat_id, user_id, user_message, bot_response, 
                       timestamp, message_id, is_quote
                FROM dialogue_context
                WHERE message_id = ?
                LIMIT 1
            """, (message_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return DialogueTurn(
                    id=row[0],
                    chat_id=row[1],
                    user_id=row[2],
                    user_message=row[3],
                    bot_response=row[4],
                    timestamp=row[5],
                    message_id=row[6],
                    is_quote=bool(row[7])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска сообщения бота: {e}")
            return None
    
    def cleanup_old_dialogues(self, max_age_hours: int = 24):
        """Очищает старые диалоги"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM dialogue_context
                WHERE timestamp < ?
            """, (cutoff_time,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"🗑️ Удалено {deleted_count} старых диалогов")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых диалогов: {e}")
    
    def format_dialogue_context(self, turns: List[DialogueTurn]) -> str:
        """Форматирует контекст диалога для промпта"""
        if not turns:
            return ""
        
        context_lines = ["=== КОНТЕКСТ ДИАЛОГА ==="]
        
        for turn in turns:
            # Форматируем время
            time_str = time.strftime('%H:%M', time.localtime(turn.timestamp))
            
            # Добавляем ход диалога
            context_lines.append(f"[{time_str}] Пользователь: {turn.user_message}")
            context_lines.append(f"[{time_str}] Бот: {turn.bot_response}")
            
            if turn.is_quote:
                context_lines.append("(Это был ответ на цитирование)")
            
            context_lines.append("")  # Пустая строка между ходами
        
        return "\n".join(context_lines)

# Глобальный экземпляр менеджера
_dialogue_manager = None

def get_dialogue_context_manager() -> DialogueContextManager:
    """Получает глобальный экземпляр менеджера диалогов"""
    global _dialogue_manager
    if _dialogue_manager is None:
        _dialogue_manager = DialogueContextManager()
    return _dialogue_manager

