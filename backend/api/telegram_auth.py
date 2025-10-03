"""
Модуль авторизации для Telegram бота.
Управляет доступом через секретное слово и защищает от спама.
"""

import sqlite3
import time
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Константы
SECRET_WORD = "MYSELF"
MAX_ATTEMPTS_PER_MINUTE = 10
BAN_DURATION_HOURS = 24

class TelegramAuth:
    """Класс для управления авторизацией пользователей."""
    
    def __init__(self, db_path: str = "backend/data/telegram_auth.db"):
        """Инициализация системы авторизации."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица авторизованных пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS authorized_users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    authorized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица попыток ввода секретного слова
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    attempt_text TEXT,
                    is_correct BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица заблокированных пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id TEXT PRIMARY KEY,
                    reason TEXT,
                    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    banned_until TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ База данных авторизации инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
    
    def is_user_authorized(self, user_id: str) -> bool:
        """Проверяет, авторизован ли пользователь."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT user_id FROM authorized_users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            conn.close()
            return result is not None
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки авторизации: {e}")
            return False
    
    def is_user_banned(self, user_id: str) -> bool:
        """Проверяет, заблокирован ли пользователь."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT banned_until FROM banned_users 
                WHERE user_id = ? AND (banned_until IS NULL OR banned_until > ?)
            ''', (user_id, datetime.now()))
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки блокировки: {e}")
            return False
    
    def get_attempts_count(self, user_id: str, minutes: int = 1) -> int:
        """Получает количество попыток за последние N минут."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            time_threshold = datetime.now() - timedelta(minutes=minutes)
            cursor.execute('''
                SELECT COUNT(*) FROM auth_attempts 
                WHERE user_id = ? AND timestamp > ?
            ''', (user_id, time_threshold))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Ошибка подсчета попыток: {e}")
            return 0
    
    def record_attempt(self, user_id: str, attempt_text: str, is_correct: bool):
        """Записывает попытку ввода секретного слова."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO auth_attempts (user_id, attempt_text, is_correct)
                VALUES (?, ?, ?)
            ''', (user_id, attempt_text, is_correct))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📝 Записана попытка для {user_id}: {'✅' if is_correct else '❌'}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи попытки: {e}")
    
    def authorize_user(self, user_id: str, username: str = None, 
                      first_name: str = None, last_name: str = None):
        """Авторизует пользователя."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO authorized_users 
                (user_id, username, first_name, last_name, authorized_at, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name, last_name))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Пользователь {user_id} авторизован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка авторизации пользователя: {e}")
    
    def ban_user(self, user_id: str, reason: str = "Превышен лимит попыток"):
        """Блокирует пользователя."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            banned_until = datetime.now() + timedelta(hours=BAN_DURATION_HOURS)
            
            cursor.execute('''
                INSERT OR REPLACE INTO banned_users 
                (user_id, reason, banned_at, banned_until)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?)
            ''', (user_id, reason, banned_until))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"🚫 Пользователь {user_id} заблокирован до {banned_until}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка блокировки пользователя: {e}")
    
    def update_last_activity(self, user_id: str):
        """Обновляет время последней активности."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE authorized_users 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления активности: {e}")
    
    def process_auth_attempt(self, user_id: str, message_text: str, 
                           username: str = None, first_name: str = None, 
                           last_name: str = None) -> Dict[str, any]:
        """
        Обрабатывает попытку авторизации.
        
        Returns:
            Dict с ключами:
            - authorized: bool - авторизован ли пользователь
            - banned: bool - заблокирован ли пользователь
            - attempts_exceeded: bool - превышен ли лимит попыток
            - message: str - сообщение для пользователя
        """
        # Проверяем блокировку
        if self.is_user_banned(user_id):
            return {
                "authorized": False,
                "banned": True,
                "attempts_exceeded": False,
                "message": f"🚫 Вы заблокированы за превышение лимита попыток. Блокировка снята через {BAN_DURATION_HOURS} часов."
            }
        
        # Проверяем количество попыток
        attempts_count = self.get_attempts_count(user_id)
        if attempts_count >= MAX_ATTEMPTS_PER_MINUTE:
            self.ban_user(user_id)
            return {
                "authorized": False,
                "banned": True,
                "attempts_exceeded": True,
                "message": f"🚫 Превышен лимит попыток ({MAX_ATTEMPTS_PER_MINUTE} в минуту). Вы заблокированы на {BAN_DURATION_HOURS} часов."
            }
        
        # Проверяем секретное слово
        is_correct = message_text.strip().upper() == SECRET_WORD
        self.record_attempt(user_id, message_text, is_correct)
        
        if is_correct:
            # Авторизуем пользователя
            self.authorize_user(user_id, username, first_name, last_name)
            return {
                "authorized": True,
                "banned": False,
                "attempts_exceeded": False,
                "message": "✅ Авторизация успешна! Теперь вы можете использовать бота."
            }
        else:
            # Неправильное слово
            remaining_attempts = MAX_ATTEMPTS_PER_MINUTE - attempts_count - 1
            return {
                "authorized": False,
                "banned": False,
                "attempts_exceeded": False,
                "message": f"❌ Неверное секретное слово. Осталось попыток: {remaining_attempts}"
            }
    
    def get_auth_stats(self) -> Dict[str, any]:
        """Получает статистику авторизации."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Количество авторизованных пользователей
            cursor.execute('SELECT COUNT(*) FROM authorized_users')
            authorized_count = cursor.fetchone()[0]
            
            # Количество заблокированных пользователей
            cursor.execute('SELECT COUNT(*) FROM banned_users WHERE banned_until > ?', (datetime.now(),))
            banned_count = cursor.fetchone()[0]
            
            # Общее количество попыток за последние 24 часа
            time_threshold = datetime.now() - timedelta(hours=24)
            cursor.execute('SELECT COUNT(*) FROM auth_attempts WHERE timestamp > ?', (time_threshold,))
            attempts_24h = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "authorized_users": authorized_count,
                "banned_users": banned_count,
                "attempts_24h": attempts_24h
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {"authorized_users": 0, "banned_users": 0, "attempts_24h": 0}


# Глобальный экземпляр для использования в других модулях
telegram_auth = TelegramAuth() 