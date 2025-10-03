"""
Модуль с исправлениями для групповых функций Telegram бота.
"""
import logging
import sqlite3
import time
from typing import List, Tuple, Optional

logger = logging.getLogger("chatumba.telegram")

async def handle_names_command(sqlite_storage, chat_id: str, from_user_id: str, send_telegram_message):
    """
    Обрабатывает команду /names.
    """
    # Устанавливаем режим сбора имен
    from backend.api.telegram_core import group_names_mode
    group_names_mode[chat_id] = 'collecting'
    
    # Сохраняем режим в базу данных
    try:
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO group_modes (chat_id, mode, last_updated) VALUES (?, ?, ?) ON CONFLICT(chat_id) DO UPDATE SET mode = ?, last_updated = ?',
            (chat_id, 'collecting', int(time.time()), 'collecting', int(time.time()))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при сохранении режима группы: {e}")
    
    # Отправляем сообщение с инструкциями
    await send_telegram_message(
        chat_id,
        "🔍 <b>Режим сбора имён активирован!</b>\n\n"
        "Укажите имена участников в формате:\n"
        "<code>@username Имя</code> или <code>@user_id Имя</code>\n\n"
        "Команды:\n"
        "• /nameslist - показать собранные имена\n"
        "• /namesdone - завершить сбор имён\n"
        "• /namescancel - отменить сбор имён",
        "HTML"
    )
    
    logger.info(f"[ГРУППА {chat_id}] Включён режим сбора имён пользователем {from_user_id}")

async def handle_nameslist_command(sqlite_storage, chat_id: str, send_telegram_message):
    """
    Обрабатывает команду /nameslist.
    """
    # Получаем список имен
    try:
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name FROM group_user_names WHERE chat_id = ?', (chat_id,))
        names = cursor.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при получении имен группы: {e}")
        names = []
    
    # Отправляем сообщение со списком имен
    if names:
        names_text = "\n".join([f"• <code>{uid}</code>: <b>{name}</b>" for uid, name in names])
        await send_telegram_message(
            chat_id,
            f"📋 <b>Собранные имена ({len(names)}):</b>\n\n{names_text}",
            "HTML"
        )
    else:
        await send_telegram_message(
            chat_id,
            "❌ Имена ещё не собраны. Используйте формат <code>@username Имя</code>",
            "HTML"
        )
    
    logger.info(f"[ГРУППА {chat_id}] Запрошен список имён, найдено: {len(names)}")

async def handle_namescancel_command(sqlite_storage, chat_id: str, send_telegram_message):
    """
    Обрабатывает команду /namescancel.
    """
    # Сбрасываем режим
    from backend.api.telegram_core import group_names_mode
    if chat_id in group_names_mode:
        del group_names_mode[chat_id]
    
    # Сохраняем режим в базу данных
    try:
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM group_modes WHERE chat_id = ?', (chat_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при удалении режима группы: {e}")
    
    # Отправляем сообщение
    await send_telegram_message(
        chat_id,
        "❌ Режим сбора имён отменён.",
        "HTML"
    )
    
    logger.info(f"[ГРУППА {chat_id}] Режим сбора имён отменён")

async def handle_namesdone_command(sqlite_storage, chat_id: str, send_telegram_message, analyze_group_history):
    """
    Обрабатывает команду /namesdone.
    """
    # Получаем список имен
    try:
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name FROM group_user_names WHERE chat_id = ?', (chat_id,))
        names = cursor.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при получении имен группы: {e}")
        names = []
    
    # Проверяем, есть ли имена
    if not names:
        await send_telegram_message(
            chat_id,
            "❌ Не найдено ни одного имени! Сначала добавьте имена в формате <code>@username Имя</code>",
            "HTML"
        )
        logger.info(f"[ГРУППА {chat_id}] Попытка завершить сбор имён, но имена не найдены")
        return
    
    # Устанавливаем активный режим
    from api.telegram_core import group_names_mode
    group_names_mode[chat_id] = 'active'
    
    # Сохраняем режим в базу данных
    try:
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO group_modes (chat_id, mode, last_updated) VALUES (?, ?, ?) ON CONFLICT(chat_id) DO UPDATE SET mode = ?, last_updated = ?',
            (chat_id, 'active', int(time.time()), 'active', int(time.time()))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при сохранении режима группы: {e}")
    
    # Отправляем сообщение
    await send_telegram_message(
        chat_id,
        f"✅ <b>Сбор имён завершён!</b>\n\nСобрано {len(names)} имён. Теперь я могу работать с группой.\n\n"
        "Команды:\n"
        "• /analyze - анализ ситуации в группе\n"
        "• /init - полный анализ всей истории группы\n"
        "• Упоминание <b>ЧАТУМБА</b> в сообщении - быстрый анализ настроения",
        "HTML"
    )
    
    logger.info(f"[ГРУППА {chat_id}] Режим сбора имён завершён, собрано {len(names)} имён")
    
    # Запускаем анализ группы и создание души
    await analyze_group_history(chat_id, reason='создание души')

async def handle_bot_added_to_group(chat_id: str, send_telegram_message):
    """
    Обрабатывает добавление бота в группу.
    """
    await send_telegram_message(
        chat_id,
        "👋 <b>Привет! Я Чатумба - бот с душой!</b>\n\n"
        "Для работы со мной в группе:\n"
        "1. Используйте /names для начала сбора имён участников\n"
        "2. Укажите имена в формате <code>@username Имя</code>\n"
        "3. Просмотрите список имён командой /nameslist\n"
        "4. Завершите сбор командой /namesdone\n"
        "5. Используйте <b>ЧАТУМБА</b> в сообщении для вызова анализа группы\n\n"
        "Я буду анализировать атмосферу в группе и создам групповую душу!",
        "HTML"
    )
    
    logger.info(f"[ГРУППА {chat_id}] Бот добавлен в группу, отправлено приветствие")

async def process_name_assignment(sqlite_storage, chat_id: str, text: str, from_user: dict, message: dict, send_telegram_message):
    """
    Обрабатывает назначение имени пользователю.
    """
    import re
    match = re.match(r"@(\w+|\d+)\s+(.+)", text)
    if not match:
        await send_telegram_message(
            chat_id,
            "❌ Неверный формат. Используйте: <code>@username Имя</code>",
            "HTML"
        )
        return
    
    mention, name = match.groups()
    name = name.strip()
    from_user_id = from_user.get("id", "")
    
    # Определяем user_id по username или числу
    target_user_id = None
    
    # Если это user_id (число)
    if mention.isdigit():
        target_user_id = mention
    else:
        # Поиск user_id по username среди последних сообщений группы
        group_msgs = sqlite_storage.get_group_messages(chat_id)
        for msg in reversed(group_msgs):
            u = msg.get("user_id", "")
            uname = msg.get("username", "")
            if uname == mention or (msg.get("from_username") == mention):
                target_user_id = u
                break
        
        # Проверяем entities для упоминаний
        if not target_user_id and "entities" in message:
            for ent in message["entities"]:
                if ent.get("type") == "mention":
                    if text[ent["offset"]+1:ent["offset"]+ent["length"]] == mention:
                        target_user_id = from_user_id
                        break
    
    # Если не удалось определить user_id
    if not target_user_id:
        await send_telegram_message(
            chat_id,
            f"❌ Не удалось определить пользователя по @{mention}. Попробуйте использовать ID пользователя.",
            "HTML"
        )
        logger.warning(f"[ГРУППА {chat_id}] Не удалось определить пользователя по @{mention}")
        return
    
    # Сохраняем имя
    sqlite_storage.set_group_user_name(chat_id, target_user_id, name)
    
    # Отправляем подтверждение
    await send_telegram_message(
        chat_id,
        f"✅ Пользователь <code>{target_user_id}</code> теперь известен как <b>{name}</b>",
        "HTML"
    )
    
    logger.info(f"[ГРУППА {chat_id}] Назначено имя участнику {target_user_id}: {name}")

def load_group_modes_from_db(sqlite_storage):
    """
    Загружает режимы групп из базы данных в память.
    """
    try:
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='group_modes'")
        if not cursor.fetchone():
            logger.info("Таблица group_modes не существует, создаем...")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_modes (
                chat_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                last_updated INTEGER NOT NULL
            )
            ''')
            conn.commit()
            conn.close()
            return {}
        
        # Получаем режимы
        cursor.execute('SELECT chat_id, mode FROM group_modes')
        modes = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        # Обновляем глобальный словарь
        from api.telegram_core import group_names_mode
        group_names_mode.update(modes)
        
        logger.info(f"Загружено {len(modes)} режимов групп из базы данных")
        return modes
    except Exception as e:
        logger.error(f"Ошибка при загрузке режимов групп: {e}")
        return {}