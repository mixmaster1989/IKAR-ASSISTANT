"""
Модуль для работы с SQLite как fallback хранилищем.
"""
import os
import logging
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

from backend.config import SQLITE_CONFIG

logger = logging.getLogger("chatumba.sqlite")

class SQLiteStorage:
    """
    Класс для работы с SQLite хранилищем.
    Используется как fallback для хранения истории чата и метаданных.
    """
    
    def __init__(self):
        """
        Инициализирует SQLite хранилище.
        """
        self.db_path = SQLITE_CONFIG["path"]
        
        # Создаем директорию для базы данных, если она не существует
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Инициализируем базу данных
        self._init_db()
    
    def _init_db(self):
        """
        Инициализирует базу данных.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создаем таблицу для истории чата
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                processed BOOLEAN DEFAULT FALSE
            )
            ''')
            
            # Создаем таблицу для метаданных пользователей
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_metadata (
                user_id TEXT PRIMARY KEY,
                last_interaction INTEGER NOT NULL,
                conversation_count INTEGER DEFAULT 0,
                metadata TEXT
            )
            ''')
            
            # Создаем таблицу для настроек пользователей
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                personality TEXT,
                last_updated INTEGER NOT NULL
            )
            ''')
            
            # Создаем таблицу для истории сообщений групп
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                message_id INTEGER,
                user_id TEXT,
                type TEXT NOT NULL, -- text/voice
                content TEXT,
                timestamp INTEGER NOT NULL
            )
            ''')
            
            # Создаем таблицу для хранения времени последней оценки группы
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_last_eval (
                chat_id TEXT PRIMARY KEY,
                last_eval_ts INTEGER NOT NULL
            )
            ''')
            
            # Создаем таблицу для хранения имён пользователей в группах
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_user_names (
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                name TEXT,
                PRIMARY KEY (chat_id, user_id)
            )
            ''')
            
            # Создаем таблицу для хранения групповых душ
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_souls (
                chat_id TEXT PRIMARY KEY,
                soul_json TEXT
            )
            ''')
            
            # Создаем таблицу для хранения режимов групп
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_modes (
                chat_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                last_updated INTEGER NOT NULL
            )
            ''')
            
            # Создаем таблицу для хранения сообщений с фото, ожидающих подтверждения
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_photo_messages (
                chat_id TEXT,
                message_id INTEGER,
                user_id TEXT,
                message_json TEXT,
                timestamp INTEGER,
                PRIMARY KEY (chat_id, message_id)
            )
            ''')
            
            # Создаем индексы
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp)')
            
            # Добавляем столбец processed если его нет
            try:
                cursor.execute('ALTER TABLE chat_history ADD COLUMN processed BOOLEAN DEFAULT FALSE')
                logger.info("✅ Столбец processed добавлен в chat_history")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.info("✅ Столбец processed уже существует")
                else:
                    raise e
            
            # Создаем индекс для processed
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_processed ON chat_history(processed)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_group_history_chat_id ON group_history(chat_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_group_history_timestamp ON group_history(timestamp)')
            
            conn.commit()
            conn.close()
            
            logger.info("SQLite база данных инициализирована")
            logger.info(f"✅ Таблицы созданы в: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации SQLite: {e}")
            logger.error(f"Путь к базе: {self.db_path}")
            raise
    
    def add_message(self, user_id: Union[str, int], role: str, content: str) -> bool:
        """
        Добавляет сообщение в историю чата.
        
        Args:
            user_id: ID пользователя
            role: Роль (user или assistant)
            content: Текст сообщения
            
        Returns:
            True, если сообщение успешно добавлено, иначе False
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Добавляем сообщение
            cursor.execute(
                'INSERT INTO chat_history (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
                (str(user_id), role, content, int(time.time()))
            )
            
            # Обновляем метаданные пользователя
            cursor.execute(
                '''
                INSERT INTO user_metadata (user_id, last_interaction, conversation_count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    last_interaction = ?,
                    conversation_count = conversation_count + 1
                ''',
                (str(user_id), int(time.time()), int(time.time()))
            )
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении сообщения в SQLite: {e}")
            return False
    
    def get_chat_history(self, user_id: Union[str, int], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получает историю чата пользователя.
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество сообщений
            
        Returns:
            Список сообщений
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Получаем историю чата
            cursor.execute(
                '''
                SELECT role, content, timestamp
                FROM chat_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                ''',
                (str(user_id), limit)
            )
            
            # Формируем результат
            history = []
            for row in cursor.fetchall():
                history.append({
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"]
                })
            
            conn.close()
            
            # Возвращаем историю в хронологическом порядке (старые сообщения в начале)
            return list(reversed(history))
        except Exception as e:
            logger.error(f"Ошибка при получении истории чата из SQLite: {e}")
            return []
    
    def clear_chat_history(self, user_id: Union[str, int]) -> bool:
        """
        Очищает историю чата пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True, если история успешно очищена, иначе False
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Удаляем историю чата
            cursor.execute(
                'DELETE FROM chat_history WHERE user_id = ?',
                (str(user_id),)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Очищена история чата пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при очистке истории чата в SQLite: {e}")
            return False
    
    def save_user_settings(self, user_id: Union[str, int], personality: Dict[str, Any]) -> bool:
        """
        Сохраняет настройки пользователя.
        
        Args:
            user_id: ID пользователя
            personality: Настройки личности
            
        Returns:
            True, если настройки успешно сохранены, иначе False
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Сохраняем настройки
            cursor.execute(
                '''
                INSERT INTO user_settings (user_id, personality, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    personality = ?,
                    last_updated = ?
                ''',
                (
                    str(user_id),
                    json.dumps(personality, ensure_ascii=False),
                    int(time.time()),
                    json.dumps(personality, ensure_ascii=False),
                    int(time.time())
                )
            )
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек пользователя в SQLite: {e}")
            return False
    
    def get_all_user_ids(self) -> List[str]:
        """
        Возвращает список всех user_id из user_metadata.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM user_metadata')
            user_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            return user_ids
        except Exception as e:
            logger.error(f"Ошибка при получении всех user_id из SQLite: {e}")
            return []

    def save_group_message(self, chat_id: str, message_id: int, user_id: str, msg_type: str, content: str, timestamp: int) -> bool:
        """
        Сохраняет сообщение группы (текст или голосовое).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO group_history (chat_id, message_id, user_id, type, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (chat_id, message_id, user_id, msg_type, content, timestamp)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении group-сообщения: {e}")
            return False

    def get_group_messages(self, chat_id: str, after_ts: int = None, before_ts: int = None) -> list:
        """
        Получает сообщения группы за период (от after_ts до before_ts, если указаны).
        Возвращает список dict.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = 'SELECT * FROM group_history WHERE chat_id = ?'
            params = [chat_id]
            if after_ts is not None:
                query += ' AND timestamp > ?'
                params.append(after_ts)
            if before_ts is not None:
                query += ' AND timestamp <= ?'
                params.append(before_ts)
            query += ' ORDER BY timestamp ASC'
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка при получении group-сообщений: {e}")
            return []

    def get_group_message(self, chat_id: str, message_id: int) -> dict:
        """
        Получает конкретное сообщение группы по message_id.
        Возвращает dict или None, если не найдено.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM group_history WHERE chat_id = ? AND message_id = ?', (chat_id, message_id))
            row = cursor.fetchone()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении group-сообщения: {e}")
            return None

    def set_group_last_eval(self, chat_id: str, last_eval_ts: int) -> bool:
        """
        Сохраняет время последней оценки группы.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO group_last_eval (chat_id, last_eval_ts) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET last_eval_ts = ?',
                (chat_id, last_eval_ts, last_eval_ts)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении времени последней оценки группы: {e}")
            return False

    def get_group_last_eval(self, chat_id: str) -> int:
        """
        Получает время последней оценки группы (timestamp). Если нет — возвращает None.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT last_eval_ts FROM group_last_eval WHERE chat_id = ?', (chat_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении времени последней оценки группы: {e}")
            return None

    def set_group_user_name(self, chat_id: str, user_id: str, name: str) -> bool:
        """
        Сохраняет имя пользователя в группе.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO group_user_names (chat_id, user_id, name) VALUES (?, ?, ?) ON CONFLICT(chat_id, user_id) DO UPDATE SET name = ?',
                (chat_id, user_id, name, name)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении group user name: {e}")
            return False

    def get_group_user_name(self, chat_id: str, user_id: str) -> str:
        """
        Получает имя пользователя в группе. Если не найдено — возвращает None.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM group_user_names WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении group user name: {e}")
            return None

    def get_group_names(self, chat_id: str) -> List[Tuple[str, str]]:
        """
        Получает все имена пользователей в группе.
        Возвращает список кортежей (user_id, name).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, name FROM group_user_names WHERE chat_id = ?', (chat_id,))
            names = cursor.fetchall()
            conn.close()
            return names
        except Exception as e:
            logger.error(f"Ошибка при получении имен группы: {e}")
            return []

    def set_group_mode(self, chat_id: str, mode: str) -> bool:
        """
        Сохраняет режим группы в базе данных.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO group_modes (chat_id, mode, last_updated) VALUES (?, ?, ?) ON CONFLICT(chat_id) DO UPDATE SET mode = ?, last_updated = ?',
                (chat_id, mode, int(time.time()), mode, int(time.time()))
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении режима группы: {e}")
            return False

    def get_group_mode(self, chat_id: str) -> str:
        """
        Получает режим группы из базы данных.
        Возвращает режим или None, если не найден.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT mode FROM group_modes WHERE chat_id = ?', (chat_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении режима группы: {e}")
            return None

    def set_group_soul(self, chat_id: str, soul_dict: dict) -> bool:
        """
        Сохраняет параметры групповой души (dict) в базе.
        """
        import json
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO group_souls (chat_id, soul_json) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET soul_json = ?',
                (chat_id, json.dumps(soul_dict, ensure_ascii=False), json.dumps(soul_dict, ensure_ascii=False))
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении групповой души: {e}")
            return False

    def get_group_soul(self, chat_id: str) -> dict:
        """
        Загружает параметры групповой души (dict) из базы. Если нет — возвращает None.
        """
        import json
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT soul_json FROM group_souls WHERE chat_id = ?', (chat_id,))
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"Ошибка при загрузке групповой души: {e}")
            return None

    def save_pending_photo(self, chat_id: str, message_id: int, user_id: str, message_dict: dict, timestamp: int) -> bool:
        """Сохраняет сообщение с фото, ожидающее подтверждения, в БД."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_photo_messages (
                    chat_id TEXT,
                    message_id INTEGER,
                    user_id TEXT,
                    message_json TEXT,
                    timestamp INTEGER,
                    PRIMARY KEY (chat_id, message_id)
                )
            ''')
            cursor.execute('''
                INSERT OR REPLACE INTO pending_photo_messages (chat_id, message_id, user_id, message_json, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, message_id, user_id, json.dumps(message_dict), timestamp))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении pending_photo_message: {e}")
            return False

    def get_pending_photo(self, chat_id: str, message_id: int) -> Optional[dict]:
        """Возвращает сообщение с фото из БД по chat_id и message_id."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT message_json FROM pending_photo_messages WHERE chat_id = ? AND message_id = ?
            ''', (chat_id, message_id))
            row = cursor.fetchone()
            conn.close()
            if row:
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении pending_photo_message: {e}")
            return None

    def delete_pending_photo(self, chat_id: str, message_id: int) -> bool:
        """Удаляет сообщение с фото из БД."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM pending_photo_messages WHERE chat_id = ? AND message_id = ?
            ''', (chat_id, message_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении pending_photo_message: {e}")
            return False

    def cleanup_old_pending_photos(self, max_age_seconds: int = 3600) -> bool:
        """Удаляет старые сообщения с фото из БД (старше max_age_seconds)."""
        try:
            import time
            cutoff = int(time.time()) - max_age_seconds
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM pending_photo_messages WHERE timestamp < ?
            ''', (cutoff,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при очистке старых pending_photo_messages: {e}")
            return False

    def get_unprocessed_messages(self, user_id: Union[str, int] = None) -> List[Dict[str, Any]]:
        """Получает необработанные сообщения (processed = FALSE)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT id, user_id, role, content, timestamp 
                    FROM chat_history 
                    WHERE processed = FALSE AND user_id = ?
                    ORDER BY timestamp
                ''', (str(user_id),))
            else:
                cursor.execute('''
                    SELECT id, user_id, role, content, timestamp 
                    FROM chat_history 
                    WHERE processed = FALSE
                    ORDER BY user_id, timestamp
                ''')
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row[0],
                    'user_id': row[1],
                    'role': row[2],
                    'content': row[3],
                    'timestamp': row[4]
                })
            
            conn.close()
            return messages
            
        except Exception as e:
            logger.error(f"Ошибка получения необработанных сообщений: {e}")
            return []
    
    def mark_message_processed(self, message_id: int) -> bool:
        """Отмечает сообщение как обработанное"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE chat_history 
                SET processed = TRUE 
                WHERE id = ?
            ''', (message_id,))
            
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return updated
            
        except Exception as e:
            logger.error(f"Ошибка отметки сообщения как обработанного: {e}")
            return False
    
    def mark_user_messages_processed(self, user_id: Union[str, int]) -> bool:
        """Отмечает все сообщения пользователя как обработанные"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE chat_history 
                SET processed = TRUE 
                WHERE user_id = ? AND processed = FALSE
            ''', (str(user_id),))
            
            updated_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if updated_count > 0:
                logger.info(f"Отмечено {updated_count} сообщений пользователя {user_id} как обработанные")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отметки сообщений пользователя как обработанных: {e}")
            return False

# Экземпляр для глобального использования
sqlite_storage = SQLiteStorage()