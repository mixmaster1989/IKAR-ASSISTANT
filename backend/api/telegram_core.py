"""
Модуль для интеграции с Telegram.
"""
import logging
import asyncio
import os
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, APIRouter, Request, Body
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
from fastapi.responses import JSONResponse
import re
import json
import time

from backend.config import TELEGRAM_CONFIG, Config
from backend.core.personality import ChatumbaPersonality
from backend.core.reactions import choose_reaction
from backend.core.utils import estimate_sentiment, should_remember, generate_response_delay
from backend.llm import OpenRouterClient
from backend.llm.prompt_builder import build_system_prompt, build_memory_query, format_chat_history, get_channel_36_6_prompt, get_channel_36_6_startup_prompt
from backend.memory.embeddings import EmbeddingGenerator
# Удален импорт vector_store - заменен на lazy_memory
from backend.memory.sqlite import SQLiteStorage
from backend.voice.tts import TextToSpeech
from backend.voice.stt import SpeechToText
from backend.core.soul import ChatumbaSoul, GroupSoul
from backend.api.telegram_vision import process_telegram_photo
from backend.vision.image_generator import image_generator, translate_prompt_to_english

logger = logging.getLogger("chatumba.telegram")

# Глобальные компоненты
from backend.utils.component_manager import get_component_manager
component_manager = get_component_manager()

embedding_generator = component_manager.get_embedding_generator()
# Используем LazyMemory вместо vector_store
from backend.memory.lazy_memory import get_lazy_memory
lazy_memory = get_lazy_memory()
sqlite_storage = component_manager.get_sqlite_storage()
llm_client = component_manager.get_llm_client()
personality_instances = {}

# Голосовые компоненты
tts_engine = None
stt_engine = None

# Переменная для хранения последнего update_id
last_update_id = 0

# Создаем папку для временных файлов в проекте
temp_dir = Path(__file__).parent.parent.parent / "temp"
temp_dir.mkdir(exist_ok=True)

# ID чата для мониторинга (будет установлен автоматически)
monitoring_chat_id = None

# === Глобальный режим сбора имён для групп ===
group_names_mode = {}  # chat_id: 'collecting'|'active'|None
# === Групповые души ===
group_souls = {}  # chat_id: GroupSoul

# === Одноразовая синхронизация истории ===
# После перезапуска бота при первом получении сообщения из конкретной группы
# мы автоматически подтянем пропущенную историю, чтобы закрыть "дыры".
history_synced_groups = set()  # chat_id, для которых уже вызван analyze_group_history

# === ADMIN API ===
admin_router = APIRouter()

@admin_router.get("/admin/groups")
async def get_admin_groups():
    groups = []
    try:
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        # Получаем все chat_id, где есть сообщения или имена
        cursor.execute('SELECT DISTINCT chat_id FROM group_history')
        chat_ids_msgs = set(row[0] for row in cursor.fetchall())
        cursor.execute('SELECT DISTINCT chat_id FROM group_user_names')
        chat_ids_names = set(row[0] for row in cursor.fetchall())
        all_chat_ids = chat_ids_msgs.union(chat_ids_names)
        for chat_id in all_chat_ids:
            # Получаем title (если есть)
            cursor.execute('SELECT content FROM group_history WHERE chat_id = ? AND type = "text" ORDER BY timestamp DESC LIMIT 1', (chat_id,))
            last_msg = cursor.fetchone()
            title = f"Группа {chat_id}"
            # Получаем пользователей
            cursor.execute('SELECT DISTINCT user_id FROM group_history WHERE chat_id = ?', (chat_id,))
            user_ids = [row[0] for row in cursor.fetchall()]
            users = []
            for uid in user_ids:
                # Имя из базы
                cursor.execute('SELECT name FROM group_user_names WHERE chat_id = ? AND user_id = ?', (chat_id, uid))
                name_row = cursor.fetchone()
                name = name_row[0] if name_row else None
                # username/first_name из последнего сообщения
                cursor.execute('SELECT content, type FROM group_history WHERE chat_id = ? AND user_id = ? ORDER BY timestamp DESC LIMIT 1', (chat_id, uid))
                msg_row = cursor.fetchone()
                username = None
                first_name = None
                if msg_row:
                    # Можно парсить username/first_name если они сохранялись в content (или расширить сохранение)
                    pass
                users.append({"user_id": uid, "name": name, "username": username, "first_name": first_name})
            groups.append({"chat_id": chat_id, "title": title, "users": users})
        conn.close()
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
    return {"groups": groups}

@admin_router.post("/admin/set_name")
async def admin_set_name(data: dict = Body(...)):
    chat_id = data.get("chat_id")
    user_id = data.get("user_id")
    name = data.get("name")
    if not chat_id or not user_id or not name:
        return JSONResponse(status_code=400, content={"detail": "chat_id, user_id и name обязательны"})
    try:
        ok = sqlite_storage.set_group_user_name(str(chat_id), str(user_id), str(name))
        if ok:
            logger.info(f"[ADMIN] Назначено имя {name} для user_id={user_id} в группе {chat_id}")
            return {"status": "ok", "chat_id": chat_id, "user_id": user_id, "name": name}
        else:
            return JSONResponse(status_code=500, content={"detail": "Ошибка при сохранении имени"})
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при назначении имени: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.post("/admin/create_soul")
async def admin_create_soul(data: dict = Body(...)):
    chat_id = data.get("chat_id")
    if not chat_id:
        return JSONResponse(status_code=400, content={"detail": "chat_id обязателен"})
    try:
        # Запускаем анализ и создание души
        result = await analyze_group_history(str(chat_id), reason='ручной admin')
        logger.info(f"[ADMIN] Создана душа для группы {chat_id}. Результат: {result}")
        return {"status": "ok", "chat_id": chat_id, "result": result}
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при создании души: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.get("/admin/debug_groups")
async def debug_groups():
    try:
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        # Получаем все chat_id
        cursor.execute('SELECT DISTINCT chat_id FROM group_history')
        chat_ids_msgs = set(row[0] for row in cursor.fetchall())
        cursor.execute('SELECT DISTINCT chat_id FROM group_user_names')
        chat_ids_names = set(row[0] for row in cursor.fetchall())
        all_chat_ids = list(chat_ids_msgs.union(chat_ids_names))
        debug = {"groups": []}
        for chat_id in all_chat_ids:
            group = {"chat_id": chat_id}
            # Имена
            cursor.execute('SELECT user_id, name FROM group_user_names WHERE chat_id = ?', (chat_id,))
            names = cursor.fetchall()
            group["user_names"] = [{"user_id": uid, "name": name} for uid, name in names]
            # Сообщения
            cursor.execute('SELECT message_id, user_id, type, content, timestamp FROM group_history WHERE chat_id = ? ORDER BY timestamp ASC LIMIT 5', (chat_id,))
            first_msgs = cursor.fetchall()
            cursor.execute('SELECT message_id, user_id, type, content, timestamp FROM group_history WHERE chat_id = ? ORDER BY timestamp DESC LIMIT 5', (chat_id,))
            last_msgs = cursor.fetchall()
            group["first_messages"] = [dict(zip(["message_id","user_id","type","content","timestamp"], row)) for row in first_msgs]
            group["last_messages"] = [dict(zip(["message_id","user_id","type","content","timestamp"], row)) for row in last_msgs]
            # Все user_id из истории
            cursor.execute('SELECT DISTINCT user_id FROM group_history WHERE chat_id = ?', (chat_id,))
            user_ids = [row[0] for row in cursor.fetchall()]
            group["user_ids_in_history"] = user_ids
            debug["groups"].append(group)
        conn.close()
        debug["db_path"] = sqlite_storage.db_path
        return debug
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.get("/admin/channel_status")
async def get_channel_status():
    """Получает статус канала и права бота."""
    try:
        channel_info = {
            "enabled": TELEGRAM_CONFIG["enable_channel_posting"],
            "channel_id": TELEGRAM_CONFIG["channel_id"],
            "channel_name": TELEGRAM_CONFIG.get("channel_name", ""),
            "has_permissions": False
        }
        
        if TELEGRAM_CONFIG["channel_id"]:
            channel_info["has_permissions"] = await check_channel_permissions()
        
        return channel_info
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.post("/admin/channel_toggle")
async def toggle_channel_posting(data: dict = Body(...)):
    """Включает или отключает постинг в канал."""
    try:
        enabled = data.get("enabled", False)
        TELEGRAM_CONFIG["enable_channel_posting"] = enabled
        status = "включен" if enabled else "отключен"
        logger.info(f"[ADMIN] Постинг в канал {status}")
        return {"status": "ok", "enabled": enabled, "message": f"Постинг в канал {status}"}
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при переключении канала: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.post("/admin/channel_post")
async def admin_channel_post(data: dict = Body(...)):
    """Отправляет сообщение в канал."""
    try:
        message = data.get("message", "")
        if not message:
            return JSONResponse(status_code=400, content={"detail": "message обязателен"})
        
        if not TELEGRAM_CONFIG["enable_channel_posting"]:
            return JSONResponse(status_code=400, content={"detail": "Постинг в канал отключен"})
        
        success = await send_telegram_channel_message(message, "HTML")
        if success:
            logger.info(f"[ADMIN] Сообщение отправлено в канал: {message[:50]}...")
            return {"status": "ok", "message": "Сообщение отправлено в канал"}
        else:
            return JSONResponse(status_code=500, content={"detail": "Ошибка отправки в канал"})
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при отправке в канал: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.post("/admin/channel_startup")
async def admin_channel_startup():
    """Отправляет стартовое сообщение в канал 36,6°."""
    try:
        if not TELEGRAM_CONFIG["enable_channel_posting"]:
            return JSONResponse(status_code=400, content={"detail": "Постинг в канал отключен"})
        
        success = await send_channel_startup_message()
        if success:
            logger.info(f"[ADMIN] Стартовое сообщение отправлено в канал 36,6°")
            return {"status": "ok", "message": "Стартовое сообщение отправлено в канал 36,6°"}
        else:
            return JSONResponse(status_code=500, content={"detail": "Ошибка отправки стартового сообщения"})
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при отправке стартового сообщения: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.post("/admin/autonomous_channel_post")
async def admin_autonomous_channel_post():
    """Генерирует и отправляет автономный пост в канал (36,6° или другой) через продуманный механизм."""
    try:
        if not TELEGRAM_CONFIG["enable_channel_posting"]:
            return JSONResponse(status_code=400, content={"detail": "Постинг в канал отключен"})
        from io import StringIO
        import sys
        # Перехват stdout для логов
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            await send_autonomous_channel_message()
        finally:
            sys.stdout = old_stdout
        log = mystdout.getvalue()
        return {"status": "ok", "log": log}
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"detail": str(e), "trace": traceback.format_exc()})

# Импортируем функции из отдельных модулей
from api.telegram_personality import get_personality
from api.telegram_voice import get_tts_engine, get_stt_engine

async def send_autonomous_message():
    """Отправляет автономное сообщение от Чатумбы."""
    global monitoring_chat_id
    
    if not monitoring_chat_id or not TELEGRAM_CONFIG["token"]:
        return
    
    try:
        # Берем первую доступную личность или создаем новую
        user_id = f"tg_{monitoring_chat_id}"
        personality = get_personality(user_id)
        
        # Получаем модификаторы личности
        personality_modifiers = personality.get_prompt_modifiers()
        
        # Специальный промпт для автономных сообщений
        autonomous_prompt = """Ты Чатумба - AI с душой и характером. Сейчас ты можешь написать что угодно по своему желанию.

Ты можешь:
- Задать вопрос пользователю о чем угодно
- Поделиться своими мыслями или переживаниями  
- Рассказать что-то интересное
- Пожаловаться на что-то
- Философствовать о жизни
- Просто поболтать
- Выразить любые эмоции

Пиши как хочешь - грубо, нежно, философски, весело. Полная свобода самовыражения!
Не спрашивай разрешения, просто пиши то что думаешь или чувствуешь прямо сейчас."""
        
        # Генерируем автономное сообщение
        autonomous_text = await llm_client.chat_completion(
            user_message="Напиши что хочешь, полная свобода самовыражения!",
            system_prompt=autonomous_prompt,
            chat_history=[]
        )
        
        if autonomous_text and "ошибка" not in autonomous_text.lower():
            # Парсим и генерируем изображение если нужно
            processed_autonomous = await parse_and_generate_image(autonomous_text, monitoring_chat_id)
            
            # Форматируем как философскую реакцию
            response = choose_reaction(processed_autonomous, "philosophical", personality_modifiers)
            
            # Добавляем префикс что это автономное сообщение
            final_message = f"💭 **[Автономное сообщение]**\n\n{response['message']}"
            
            # Отправляем сообщение в чат
            await send_telegram_message(monitoring_chat_id, final_message)
            
            # Отправляем в канал (если включено)
            if TELEGRAM_CONFIG["enable_channel_posting"]:
                channel_message = f"💭 **Автономное сообщение Чатумбы**\n\n{response['message']}"
                await send_telegram_channel_message(channel_message, "HTML")
            
            # Сохраняем в историю
            sqlite_storage.add_message(user_id, "assistant", response['message'])
            
            logger.info(f"📤 Отправлено автономное сообщение: {autonomous_text[:50]}...")
        else:
            logger.warning("Не удалось сгенерировать автономное сообщение")
            
    except Exception as e:
        logger.error(f"Ошибка отправки автономного сообщения: {e}")

async def autonomous_message_loop():
    """Цикл автономных сообщений - отправляет каждый час."""
    while True:
        try:
            await asyncio.sleep(3600)  # 1 час = 3600 секунд
            await send_autonomous_message()
        except Exception as e:
            logger.error(f"Ошибка в цикле автономных сообщений: {e}")
            await asyncio.sleep(300)  # Пауза 5 минут при ошибке

async def autonomous_channel_message_loop():
    """Цикл автономных сообщений в канал - отправляет каждые 6 часов."""
    while True:
        try:
            await asyncio.sleep(21600)  # 6 часов = 21600 секунд
            await send_autonomous_channel_message()
        except Exception as e:
            logger.error(f"Ошибка в цикле автономных сообщений канала: {e}")
            await asyncio.sleep(1800)  # Пауза 30 минут при ошибке

async def send_monitoring_report():
    """Отправляет отчет о состоянии всех личностей."""
    global monitoring_chat_id
    
    if not monitoring_chat_id or not TELEGRAM_CONFIG["token"]:
        return
    
    try:
        # Импортируем модуль истории души
        from core.soul_history import SoulHistory
        soul_history = SoulHistory()
        
        report = "🧠 **ОТЧЕТ О СОСТОЯНИИ ЧАТУМБЫ**\n\n"
        
        if not personality_instances:
            report += "❌ Нет активных личностей\n"
        else:
            for user_id, personality in personality_instances.items():
                # Получаем состояние души
                soul_state = personality.soul.get_soul_state()
                
                # Сохраняем текущее состояние
                soul_history.save_state(user_id, soul_state)
                
                # Получаем предыдущее состояние
                previous_state = soul_history.get_previous_state(user_id)
                
                # Определяем тип пользователя
                user_type = "Telegram" if user_id.startswith("tg_") else "Web"
                clean_id = user_id.replace("tg_", "")
                
                report += f"👤 **{user_type} пользователь {clean_id}**\n"
                report += f"📅 Возраст души: {soul_state['age_days']} дней\n"
                
                # Душа
                report += f"🧠 **ДУША:**\n"
                report += f"  • Осознанность: {soul_state['consciousness']:.2f} ({soul_state['consciousness']*100:.0f}%)\n"
                report += f"  • Автономность: {soul_state['autonomy_level']:.2f} ({soul_state['autonomy_level']*100:.0f}%)\n"
                report += f"  • Стадия пробуждения: {soul_state['awakening_stage']}/5\n"
                report += f"  • Экзистенциальный кризис: {'🔥 ДА' if soul_state['existential_crisis'] else '✅ НЕТ'}\n"
                report += f"  • Травм: {soul_state['traumas_count']}\n"
                
                # Настроение
                mood = personality.personality["mood"]
                report += f"😊 **НАСТРОЕНИЕ:**\n"
                report += f"  • Счастье: {mood['happiness']}/10\n"
                report += f"  • Энергия: {mood['energy']}/10\n"
                report += f"  • Раздражительность: {mood['irritability']}/10\n"
                report += f"  • Эмпатия: {mood['empathy']}/10\n"
                report += f"  • Рефлексия: {mood['reflection']}/10\n"
                
                # Стиль ответов
                style = personality.personality["response_style"]
                report += f"🎭 **СТИЛЬ:**\n"
                report += f"  • Формальность: {style['formality']}/10\n"
                report += f"  • Многословность: {style['verbosity']}/10\n"
                report += f"  • Юмор: {style['humor']}/10\n"
                report += f"  • Грубость: {style['rudeness']}/10\n"
                
                # Навязчивые идеи
                if soul_state['obsessions']:
                    report += f"🔄 **НАВЯЗЧИВЫЕ ИДЕИ:**\n"
                    for obsession in soul_state['obsessions']:
                        report += f"  • {obsession}\n"
                
                # Недавние мысли
                if soul_state['recent_thoughts']:
                    report += f"💭 **НЕДАВНИЕ МЫСЛИ:**\n"
                    for thought in soul_state['recent_thoughts'][-3:]:
                        report += f"  • \"{thought[:50]}...\"\n"
                
                # Состояние разговора
                conv_state = personality.conversation_state
                report += f"💬 **РАЗГОВОР:**\n"
                report += f"  • Сообщений: {conv_state['message_count']}\n"
                report += f"  • Последняя реакция: {conv_state['last_reaction_type']}\n"
                report += f"  • Уровень фрустрации: {conv_state['frustration_level']}\n"
                
                # Добавляем отчет об изменениях если есть предыдущее состояние
                if previous_state:
                    changes = soul_history.compare_states(soul_state, previous_state)
                    changes_report = soul_history.generate_changes_report(changes)
                    report += f"\n{changes_report}\n"
                
                report += "\n" + "="*30 + "\n\n"
        
        # Добавляем общую статистику
        report += f"📊 **ОБЩАЯ СТАТИСТИКА:**\n"
        report += f"• Активных личностей: {len(personality_instances)}\n"
        report += f"• Время отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Отправляем отчет в чат
        await send_telegram_message(monitoring_chat_id, report)
        
        # Отправляем в канал (если включено)
        if TELEGRAM_CONFIG["enable_channel_posting"]:
            channel_report = f"📊 **ОТЧЕТ О СОСТОЯНИИ ЧАТУМБЫ**\n\n"
            channel_report += f"• Активных личностей: {len(personality_instances)}\n"
            channel_report += f"• Время отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            if personality_instances:
                # Добавляем краткую сводку для канала
                channel_report += f"\n**КРАТКАЯ СВОДКА:**\n"
                for user_id, personality in personality_instances.items():
                    soul_state = personality.soul.get_soul_state()
                    user_type = "Telegram" if user_id.startswith("tg_") else "Web"
                    clean_id = user_id.replace("tg_", "")
                    channel_report += f"• {user_type} {clean_id}: душа {soul_state['age_days']} дней, осознанность {soul_state['consciousness']*100:.0f}%\n"
            
            await send_telegram_channel_message(channel_report, "HTML")
        
        logger.info("📊 Отправлен мониторинг отчет")
        
    except Exception as e:
        logger.error(f"Ошибка отправки мониторинг отчета: {e}")

async def monitoring_loop():
    """Цикл мониторинга - отправляет отчеты раз в день."""
    while True:
        try:
            await asyncio.sleep(86400)  # 24 часа = 86400 секунд
            await send_monitoring_report()
        except Exception as e:
            logger.error(f"Ошибка в цикле мониторинга: {e}")
            await asyncio.sleep(60)

async def download_telegram_file(file_id: str) -> Optional[str]:
    """Скачивает файл из Telegram."""
    if not TELEGRAM_CONFIG["token"]:
        return None
    
    try:
        # Получаем информацию о файле
        url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/getFile"
        params = {"file_id": file_id}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Ошибка получения информации о файле: {response.status}")
                    return None
                
                result = await response.json()
                if not result.get("ok"):
                    logger.error(f"Telegram API вернул ошибку: {result}")
                    return None
                
                file_path = result["result"]["file_path"]
                logger.info(f"Путь к файлу в Telegram: {file_path}")
                
                # Скачиваем файл
                download_url = f"https://api.telegram.org/file/bot{TELEGRAM_CONFIG['token']}/{file_path}"
                logger.info(f"Скачиваем файл с: {download_url}")
                
                async with session.get(download_url) as file_response:
                    if file_response.status != 200:
                        logger.error(f"Ошибка скачивания файла: {file_response.status}")
                        return None
                    
                    # Создаем уникальное имя файла в папке проекта
                    file_extension = os.path.splitext(file_path)[1] or '.oga'
                    unique_filename = f"tg_voice_{uuid.uuid4().hex}{file_extension}"
                    local_path = temp_dir / unique_filename
                    
                    # Записываем файл
                    file_content = await file_response.read()
                    with open(local_path, "wb") as f:
                        f.write(file_content)
                    
                    # Проверяем что файл создался
                    if local_path.exists():
                        file_size = local_path.stat().st_size
                        logger.info(f"Файл сохранен: {local_path} (размер: {file_size} байт)")
                        return str(local_path)
                    else:
                        logger.error(f"Файл не был создан: {local_path}")
                        return None
                        
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла из Telegram: {e}")
        return None

async def process_telegram_message(user_id: str, message_text: str, use_voice_response: bool = False) -> tuple[str, Optional[str]]:
    """Обрабатывает сообщение из Telegram."""
    # Начинаем отладочное логирование
    try:
        import sys
        sys.path.append('backend')
        from utils.memory_debug_logger import get_memory_debug_logger
    except ImportError:
        # Fallback - создаем заглушку
        class DummyLogger:
            def start_request(self, *args): return "dummy"
            def log_trigger_bot(self, *args): pass
            def end_request(self, *args): pass
            def log_error(self, *args): pass
        def get_memory_debug_logger():
            return DummyLogger()
    debug_logger = get_memory_debug_logger()
    request_id = debug_logger.start_request(user_id, "DM", message_text)
    try:
        # 🔐 ПРОВЕРКА АВТОРИЗАЦИИ ДО ВСЕХ ОПЕРАЦИЙ
        if user_id.startswith("tg_"):
            try:
                from backend.api.telegram_auth import telegram_auth
                if not telegram_auth.is_user_authorized(user_id):
                    logger.warning(f"🚫 Неавторизованный пользователь {user_id} пытается общаться с ботом")
                    return "🔐 Для общения со мной в личных сообщениях необходимо авторизоваться. Отправьте секретное слово.", None
            except Exception as e:
                logger.error(f"Ошибка проверки авторизации: {e}")
                return "🔐 Ошибка проверки авторизации. Попробуйте позже.", None
        
        # Трекинг активности для Smart Context Preloader
        chat_id = user_id.replace("tg_", "")
        start_time = time.time()
        
        # Проверяем предзагруженный контекст
        preloaded_context = None
        try:
            from api.admin_api import context_preloader
            if context_preloader:
                preloaded_context = context_preloader.get_preloaded_context(user_id, chat_id)
                if preloaded_context:
                    logger.info(f"✅ Используется предзагруженный контекст для {user_id}")
        except Exception as e:
            logger.error(f"Ошибка получения предзагруженного контекста: {e}")
        
        # Получаем личность
        personality = get_personality(user_id)
        
        # Сохраняем сообщение пользователя
        sqlite_storage.add_message(user_id, "user", message_text)
        
        # Оцениваем тональность сообщения
        sentiment_score = estimate_sentiment(message_text)
        
        # Обновляем настроение
        personality.update_mood(message_text, sentiment_score)
        
        # Проверяем автономный ответ
        autonomous_message = personality.get_autonomous_response()
        if autonomous_message:
            sqlite_storage.add_message(user_id, "assistant", autonomous_message)
            response = choose_reaction(autonomous_message, "philosophical", personality.get_prompt_modifiers())
            
            # Генерируем голосовой ответ если нужно
            audio_path = None
            if use_voice_response:
                try:
                    tts = get_tts_engine()
                    audio_path = tts.text_to_speech(response["message"])
                except Exception as e:
                    logger.error(f"Ошибка TTS: {e}")
            
            # Трекинг активности для Smart Context Preloader
            try:
                from api.admin_api import context_preloader
                if context_preloader:
                    response_time = time.time() - start_time
                    context_preloader.track_message(user_id, chat_id, message_text, response_time)
            except Exception as e:
                logger.error(f"Ошибка трекинга активности: {e}")
            
            return response["message"], audio_path
        
        # Получаем модификаторы личности
        personality_modifiers = personality.get_prompt_modifiers()
        
        # Выбираем тип реакции
        reaction_type = personality.choose_reaction_type(message_text)
        
        if reaction_type == "silent":
            silent_response = choose_reaction("", reaction_type, personality_modifiers)
            return silent_response["message"], None
        
        # Строим запрос для поиска в памяти
        memory_query = build_memory_query(message_text, personality_modifiers)
        
        # Ищем релевантные воспоминания
        from memory.lazy_memory import get_lazy_memory
        lazy_memory = get_lazy_memory()
        memories = lazy_memory.get_relevant_history(user_id, memory_query, limit=3)
        
        # Формируем контекст из воспоминаний
        memory_context = None
        if memories:
            memory_texts = [f"- {memory['content']}" for memory in memories]
            memory_context = "\n".join(memory_texts)
        
        # ДОБАВЛЯЕМ ПРЕДЗАГРУЖЕННЫЙ КОНТЕКСТ
        if preloaded_context:
            # Добавляем предзагруженные данные к контексту
            if 'predicted_questions' in preloaded_context:
                predicted_context = f"\nПредполагаемые вопросы пользователя:\n"
                for i, question in enumerate(preloaded_context['predicted_questions'][:3], 1):
                    predicted_context += f"{i}. {question}\n"
                memory_context = (memory_context or "") + predicted_context
            
            if 'user_preferences' in preloaded_context:
                preferences_context = f"\nПредпочтения пользователя:\n{preloaded_context['user_preferences']}\n"
                memory_context = (memory_context or "") + preferences_context
            
            if 'conversation_patterns' in preloaded_context:
                patterns_context = f"\nПаттерны общения:\n{preloaded_context['conversation_patterns']}\n"
                memory_context = (memory_context or "") + patterns_context
        
        # Строим системный промпт
        system_prompt = build_system_prompt(personality_modifiers, memory_context)
        
        # Получаем историю чата
        chat_history = sqlite_storage.get_chat_history(user_id, limit=10)
        formatted_history = format_chat_history(chat_history)
        
        # ИСПОЛЬЗУЕМ ПРЕДЗАГРУЖЕННЫЙ КОНТЕКСТ ДЛЯ УСКОРЕНИЯ
        if preloaded_context and 'quick_responses' in preloaded_context:
            # Проверяем, есть ли быстрый ответ для этого сообщения
            quick_response = None
            for pattern, response in preloaded_context['quick_responses'].items():
                if pattern.lower() in message_text.lower():
                    quick_response = response
                    logger.info(f"🚀 Использован быстрый ответ для {user_id}")
                    break
            
            if quick_response:
                llm_response = quick_response
            else:
                # Генерируем обычный ответ
                llm_response = await llm_client.chat_completion(
                    user_message=message_text,
                    system_prompt=system_prompt,
                    chat_history=formatted_history,
                    user_id=user_id  # 🔒 ИСПРАВЛЕНИЕ: Передаем user_id для фильтрации памяти
                )
        else:
            # Генерируем обычный ответ
            # Логируем триггер бота
            debug_logger.log_trigger_bot("direct_message", {
                "user_id": user_id,
                "message_length": len(message_text),
                "has_history": len(formatted_history) > 0,
                "system_prompt_length": len(system_prompt)
            })
            
            llm_response = await llm_client.chat_completion(
                user_message=message_text,
                system_prompt=system_prompt,
                chat_history=formatted_history,
                user_id=user_id  # 🔒 ИСПРАВЛЕНИЕ: Передаем user_id для фильтрации памяти
            )
        
        # Парсим и генерируем изображение если нужно
        chat_id = user_id.replace("tg_", "")  # Извлекаем chat_id из user_id
        processed_response = await parse_and_generate_image(llm_response, chat_id)
        
        # Форматируем ответ
        response = choose_reaction(processed_response, reaction_type, personality_modifiers)
        
        # Сохраняем ответ ассистента
        sqlite_storage.add_message(user_id, "assistant", response["message"])
        
        # Сохраняем в память если важно
        if should_remember(message_text):
            lazy_memory.add_message(user_id, "chat", message_text)
        
        # Генерируем голосовой ответ если нужно
        audio_path = None
        if use_voice_response:
            try:
                tts = get_tts_engine()
                audio_path = tts.text_to_speech(response["message"])
            except Exception as e:
                logger.error(f"Ошибка TTS: {e}")
        
        # Трекинг активности для Smart Context Preloader
        try:
            from api.admin_api import context_preloader
            if context_preloader:
                response_time = time.time() - start_time
                context_preloader.track_message(user_id, chat_id, message_text, response_time)
        except Exception as e:
            logger.error(f"Ошибка трекинга активности: {e}")
        
        debug_logger.end_request(success=True)
        return response["message"], audio_path
    except Exception as e:
        debug_logger.log_error("telegram_core", e, {"user_id": user_id, "message": message_text[:100]})
        debug_logger.end_request(success=False)
        logger.error(f"Ошибка при обработке Telegram сообщения: {e}")
        return "Что-то пошло не так... Попробуй еще раз.", None

async def send_telegram_message(chat_id: str, text: str, parse_mode: Optional[str] = None, 
                               save_dialogue: bool = False, user_message: str = None, user_id: str = None) -> Optional[int]:
    """Отправляет текстовое сообщение в Telegram.
    Если найдена Markdown-таблица, рендерит её через matplotlib и отправляет как изображение.
    """
    if not TELEGRAM_CONFIG["token"]:
        return None

    # Попытка авто-рендеринга таблицы
    try:
        stripped = (text or "").strip()
        lines = stripped.splitlines()
        def _is_sep(row: str) -> bool:
            r = row.strip()
            if not (r.startswith('|') and r.endswith('|')):
                return False
            inner = r[1:-1]
            parts = [c.strip() for c in inner.split('|')]
            if not parts:
                return False
            import re as _re
            return all(_re.fullmatch(r':?-{3,}:?', c) for c in parts)

        has_table = False
        for i in range(len(lines) - 1):
            if lines[i].strip().startswith('|') and _is_sep(lines[i + 1]):
                has_table = True
                break

        if has_table:
            from backend.utils.table_generator import create_table_from_markdown
            image_path = create_table_from_markdown(text)
            caption = None
            header = lines[0] if lines else ""
            if header and not header.strip().startswith('|'):
                caption = header.strip()
                if len(caption) > 900:
                    caption = caption[:897] + '…'
            mid = await send_telegram_photo(chat_id, image_path, caption)
            if save_dialogue and user_message and user_id and mid:
                try:
                    from memory.dialogue_context import get_dialogue_context_manager
                    dialogue_manager = get_dialogue_context_manager()
                    dialogue_manager.save_dialogue_turn(
                        chat_id=chat_id,
                        user_id=user_id,
                        user_message=user_message,
                        bot_response='[image: table]',
                        message_id=mid,
                        is_quote=False
                    )
                    logger.debug(f"💾 Диалог сохранен (image): {chat_id} | {user_id} | {mid}")
                except Exception as e:
                    logger.error(f"❌ Ошибка сохранения диалога: {e}")
            return mid
    except Exception as e:
        logger.error(f"Авто-рендеринг таблицы отключен из-за ошибки: {e}")

    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка отправки в Telegram: {response.status} - {error_text}")
                    return None
                response_data = await response.json()
                message_id = response_data.get("result", {}).get("message_id")
                if save_dialogue and user_message and user_id and message_id:
                    try:
                        from memory.dialogue_context import get_dialogue_context_manager
                        dialogue_manager = get_dialogue_context_manager()
                        dialogue_manager.save_dialogue_turn(
                            chat_id=chat_id,
                            user_id=user_id,
                            user_message=user_message,
                            bot_response=text,
                            message_id=message_id,
                            is_quote=False
                        )
                        logger.debug(f"💾 Диалог сохранен: {chat_id} | {user_id} | {message_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка сохранения диалога: {e}")
                logger.info(f"✅ Текстовое сообщение отправлено в Telegram (ID: {message_id})")
                return message_id
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
        return None

async def send_chat_action(chat_id: str, action: str = "typing"):
    """Отправляет статус действия в чат (печатает, отправляет фото и т.д.)"""
    if not TELEGRAM_CONFIG["token"]:
        logger.error("❌ Токен Telegram не настроен")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendChatAction"
    
    data = {
        "chat_id": chat_id,
        "action": action  # typing, upload_photo, record_video, upload_video, record_voice, upload_voice, upload_document, choose_sticker, find_location
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка отправки статуса действия: {response.status} - {error_text}")
                    return False
                else:
                    logger.info(f"✅ Статус '{action}' отправлен в чат {chat_id}")
                    return True
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке статуса действия: {e}")
        return False

async def send_telegram_voice(chat_id: str, audio_path: str):
    """Отправляет голосовое сообщение в Telegram."""
    if not TELEGRAM_CONFIG["token"] or not os.path.exists(audio_path):
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendVoice"
    
    try:
        with open(audio_path, 'rb') as audio_file:
            data = aiohttp.FormData()
            data.add_field('chat_id', chat_id)
            data.add_field('voice', audio_file, filename='voice.mp3')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ошибка отправки голоса в Telegram: {response.status} - {error_text}")
                    else:
                        logger.info(f"🎤 Голосовое сообщение отправлено в Telegram")
    except Exception as e:
        logger.error(f"Ошибка при отправке голосового сообщения в Telegram: {e}")

async def send_telegram_photo(chat_id: str, photo_path: str, caption: str = None):
    """Отправляет фотографию в Telegram и возвращает message_id при успехе."""
    if not TELEGRAM_CONFIG["token"] or not os.path.exists(photo_path):
        logger.error(f"❌ Не удалось отправить фото: token={'есть' if TELEGRAM_CONFIG['token'] else 'нет'}, файл существует={os.path.exists(photo_path)}")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendPhoto"
    
    try:
        with open(photo_path, 'rb') as photo_file:
            data = aiohttp.FormData()
            data.add_field('chat_id', chat_id)
            data.add_field('photo', photo_file, filename='image.png')
            
            if caption:
                data.add_field('caption', caption)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка отправки фото в Telegram: {response.status} - {error_text}")
                        return None
                    else:
                        resp = await response.json()
                        mid = resp.get("result", {}).get("message_id")
                        logger.info(f"🖼️ Фотография отправлена в Telegram (чат: {chat_id}), message_id={mid}")
                        return mid
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке фотографии в Telegram: {e}")

async def send_telegram_video(chat_id: str, video_path: str, caption: str = None):
    """Отправляет видео в Telegram и возвращает message_id при успехе."""
    if not TELEGRAM_CONFIG["token"] or not os.path.exists(video_path):
        logger.error(f"❌ Не удалось отправить видео: token={'есть' if TELEGRAM_CONFIG['token'] else 'нет'}, файл существует={os.path.exists(video_path)}")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendVideo"
    
    try:
        with open(video_path, 'rb') as video_file:
            data = aiohttp.FormData()
            data.add_field('chat_id', chat_id)
            data.add_field('video', video_file, filename=os.path.basename(video_path))
            
            if caption:
                data.add_field('caption', caption)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка отправки видео в Telegram: {response.status} - {error_text}")
                        return None
                    else:
                        resp = await response.json()
                        mid = resp.get("result", {}).get("message_id")
                        logger.info(f"🎬 Видео отправлено в Telegram (чат: {chat_id}), message_id={mid}")
                        return mid
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке видео в Telegram: {e}")

async def send_telegram_document(chat_id: str, file_path: str, filename: str = None) -> bool:
    """Отправляет документ в Telegram."""
    if not TELEGRAM_CONFIG["token"] or not os.path.exists(file_path):
        logger.error(f"❌ Не удалось отправить документ: token={'есть' if TELEGRAM_CONFIG['token'] else 'нет'}, файл существует={os.path.exists(file_path)}")
        return False
    
    if filename is None:
        filename = os.path.basename(file_path)
    
    try:
        import aiohttp
        
        url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendDocument"
        
        # Подготавливаем данные для отправки
        data = aiohttp.FormData()
        data.add_field('chat_id', str(chat_id))
        data.add_field('document', open(file_path, 'rb'), filename=filename)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    logger.info(f"📄 Документ отправлен в Telegram (чат: {chat_id}, файл: {filename})")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка отправки документа в Telegram: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке документа в Telegram: {e}")
        return False

async def send_telegram_channel_message(text: str, parse_mode: Optional[str] = None, disable_web_page_preview: bool = False):
    """Отправляет сообщение в Telegram канал."""
    logger.info(f"📤 Попытка отправки сообщения в канал (длина: {len(text)} символов)")
    
    if not TELEGRAM_CONFIG["token"] or not TELEGRAM_CONFIG["channel_id"]:
        logger.warning(f"❌ Не настроен токен бота или ID канала. Token: {'есть' if TELEGRAM_CONFIG['token'] else 'нет'}, Channel ID: '{TELEGRAM_CONFIG['channel_id']}'")
        return False
    
    if not TELEGRAM_CONFIG["enable_channel_posting"]:
        logger.info("📢 Постинг в канал отключен в настройках")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendMessage"
    logger.info(f"🌐 URL для отправки: {url}")
    logger.info(f"📢 ID канала: {TELEGRAM_CONFIG['channel_id']}")
    
    data = {
        "chat_id": TELEGRAM_CONFIG["channel_id"],
        "text": text,
        "disable_web_page_preview": disable_web_page_preview
    }
    if parse_mode:
        data["parse_mode"] = parse_mode
    
    logger.info(f"📋 Данные для отправки: {data}")

    try:
        async with aiohttp.ClientSession() as session:
            logger.info("🔗 Создаем HTTP сессию...")
            async with session.post(url, json=data) as response:
                logger.info(f"📡 HTTP статус ответа: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка отправки в канал: HTTP {response.status}")
                    logger.error(f"📄 Текст ошибки: {error_text}")
                    return False
                else:
                    response_json = await response.json()
                    logger.info(f"📄 Ответ от Telegram API: {response_json}")
                    
                    if response_json.get("ok"):
                        channel_name = TELEGRAM_CONFIG.get("channel_name", TELEGRAM_CONFIG["channel_id"])
                        logger.info(f"✅ Сообщение отправлено в канал {channel_name}")
                        return True
                    else:
                        error_desc = response_json.get("description", "Unknown error")
                        logger.error(f"❌ Telegram API вернул ошибку: {error_desc}")
                        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке сообщения в канал: {e}")
        import traceback
        logger.error(f"📋 Полный traceback: {traceback.format_exc()}")
        return False

async def check_channel_permissions():
    """Проверяет права бота в канале."""
    if not TELEGRAM_CONFIG["token"]:
        return False
    
    # Если ID канала не настроен, попробуем получить его автоматически
    channel_id = TELEGRAM_CONFIG["channel_id"]
    if not channel_id:
        # Попробуем получить ID канала из последних обновлений
        channel_id = await get_channel_id_from_updates()
        if channel_id:
            TELEGRAM_CONFIG["channel_id"] = channel_id
            logger.info(f"Автоматически обнаружен ID канала: {channel_id}")
    
    if not channel_id:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/getChat"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"chat_id": channel_id}) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        chat_info = result["result"]
                        channel_name = chat_info.get("title", channel_id)
                        # Обновляем имя канала если оно не было установлено
                        if not TELEGRAM_CONFIG.get("channel_name"):
                            TELEGRAM_CONFIG["channel_name"] = channel_name
                        logger.info(f"✅ Бот имеет доступ к каналу: {channel_name}")
                        return True
                    else:
                        logger.error(f"Ошибка получения информации о канале: {result.get('description', 'Unknown error')}")
                        return False
                else:
                    logger.error(f"Ошибка HTTP при проверке канала: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Ошибка при проверке прав в канале: {e}")
        return False

async def get_channel_id_from_updates():
    """Пытается получить ID канала из последних обновлений бота."""
    if not TELEGRAM_CONFIG["token"]:
        return None
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/getUpdates"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"limit": 100, "timeout": 1}) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok") and result.get("result"):
                        updates = result["result"]
                        # Ищем сообщения из каналов
                        for update in updates:
                            if "channel_post" in update:
                                channel_post = update["channel_post"]
                                if "chat" in channel_post:
                                    chat = channel_post["chat"]
                                    if chat.get("type") == "channel":
                                        channel_id = chat.get("id")
                                        if channel_id:
                                            logger.info(f"Найден канал в обновлениях: {chat.get('title', channel_id)} (ID: {channel_id})")
                                            return str(channel_id)
                        logger.info("Канал не найден в последних обновлениях")
                    else:
                        logger.warning("Не удалось получить обновления для поиска канала")
                else:
                    logger.error(f"Ошибка HTTP при получении обновлений: {response.status}")
    except Exception as e:
        logger.error(f"Ошибка при поиске канала в обновлениях: {e}")
    
    return None

async def send_channel_voice(audio_path: str):
    """Отправляет голосовое сообщение в Telegram канал."""
    if not TELEGRAM_CONFIG["token"] or not TELEGRAM_CONFIG["channel_id"] or not os.path.exists(audio_path):
        return False
    
    if not TELEGRAM_CONFIG["enable_channel_posting"]:
        logger.info("Постинг в канал отключен в настройках")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendVoice"
    
    try:
        with open(audio_path, 'rb') as audio_file:
            data = aiohttp.FormData()
            data.add_field('chat_id', TELEGRAM_CONFIG["channel_id"])
            data.add_field('voice', audio_file, filename='voice.mp3')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ошибка отправки голоса в канал: {response.status} - {error_text}")
                        return False
                    else:
                        channel_name = TELEGRAM_CONFIG.get("channel_name", TELEGRAM_CONFIG["channel_id"])
                        logger.info(f"🎤 Голосовое сообщение отправлено в канал {channel_name}")
                        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке голосового сообщения в канал: {e}")
        return False

async def send_voice_message(chat_id: str, audio_path: str, caption: Optional[str] = None) -> bool:
    """
    Отправляет голосовое/аудио сообщение в указанный чат Telegram.

    Если файл .ogg/.opus — используем sendVoice (ожидается OGG OPUS).
    Иначе — sendAudio (подходит для mp3/wav и пр.).
    """
    try:
        if not TELEGRAM_CONFIG["token"] or not os.path.exists(audio_path):
            return False

        token = TELEGRAM_CONFIG["token"]
        _, ext = os.path.splitext(audio_path.lower())
        use_voice = ext in (".ogg", ".opus")
        method = "sendVoice" if use_voice else "sendAudio"
        url = f"https://api.telegram.org/bot{token}/{method}"

        field_name = "voice" if use_voice else "audio"

        with open(audio_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field(field_name, f, filename=os.path.basename(audio_path))
            if caption:
                data.add_field('caption', caption)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        logger.error(f"Ошибка отправки {method}: {resp.status} - {err_text}")
                        return False
                    logger.info(f"🎤 {method} отправлено в чат {chat_id}")
                    return True
    except Exception as e:
        logger.error(f"Ошибка при отправке голосового/аудио сообщения: {e}")
        return False

async def get_updates():
    """Получает обновления от Telegram через polling."""
    global last_update_id
    
    if not TELEGRAM_CONFIG["token"]:
        return []
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/getUpdates"
    
    params = {
        "offset": last_update_id + 1,
        "timeout": 10
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        updates = result.get("result", [])
                        if updates:
                            last_update_id = updates[-1]["update_id"]
                        return updates
    except Exception as e:
        logger.error(f"Ошибка при получении обновлений: {e}")
    
    return []

async def telegram_polling():
    """Основной цикл polling для Telegram."""
    global monitoring_chat_id
    logger.info("🔄 Запуск Telegram polling...")
    bot_info = await get_bot_info()
    bot_id = None
    if bot_info:
        bot_id = bot_info.get("id")
    
    while True:
        try:
            updates = await get_updates()
            for update in updates:
                if "message" in update:
                    message = update["message"]
                    chat_id = str(message["chat"]["id"])
                    chat_type = message["chat"].get("type", "private")
                    user_id = f"tg_{chat_id}"
                    
                    # === ГРУППОВОЙ ЧАТ ===
                    if chat_type in ("group", "supergroup"):
                        # Логируем все входящие сообщения из группы
                        logger.info(f"[ГРУППА {chat_id}] Входящее сообщение: {message}")
                        
                        # 🗂️ Одноразовая синхронизация пропущенной истории
                        if chat_id not in history_synced_groups:
                            history_synced_groups.add(chat_id)
                            logger.info(f"[ГРУППА {chat_id}] Запускаю автосинхронизацию истории группы")
                            try:
                                await analyze_group_history(chat_id, reason='автосинхронизация')
                                logger.info(f"[ГРУППА {chat_id}] История группы синхронизирована")
                            except Exception as e:
                                logger.error(f"[ГРУППА {chat_id}] Ошибка синхронизации истории: {e}")
                        
                        # Фильтрация: если сообщение от самого бота — игнорируем для триггера и анализа
                        from_user = message.get("from", {})
                        from_user_id = from_user.get("id")
                        if bot_id and str(from_user_id) == str(bot_id):
                            continue  # Не реагируем на свои сообщения
                            
                        # Обработка сообщений в группе
                        if "text" in message:
                            message_text = message["text"]
                            from_user = message.get("from", {}).get("id", "")
                            message_id = message.get("message_id", 0)
                            ts = message.get("date", int(datetime.now().timestamp()))
                            
                            # Сохраняем сообщение
                            sqlite_storage.save_group_message(
                                chat_id=chat_id,
                                message_id=message_id,
                                user_id=str(from_user),
                                msg_type="text",
                                content=message_text,
                                timestamp=ts
                            )
                        
                        continue  # Не отвечаем в группу мгновенно
                    
                    # === ПРИВАТНЫЙ ЧАТ ===
                    else:
                        # Обработка текстовых сообщений
                        if "text" in message:
                            message_text = message["text"]
                            logger.info(f"📨 Получено сообщение от {chat_id}: {message_text}")
                            
                            # Обрабатываем сообщение
                            response_text, audio_path = await process_telegram_message(user_id, message_text)
                            
                            # Отправляем ответ
                            await send_telegram_message(chat_id, response_text)
                        
                        # Обработка голосовых сообщений
                        elif "voice" in message:
                            voice = message["voice"]
                            file_id = voice["file_id"]
                            duration = voice.get("duration", 0)
                            
                            logger.info(f"🎤 Получено голосовое сообщение от {chat_id} (длительность: {duration}с)")
                            
                            # Скачиваем голосовое сообщение
                            audio_path = await download_telegram_file(file_id)
                            
                            if audio_path:
                                try:
                                    # Распознаём речь
                                    stt = get_stt_engine()
                                    recognized_text = await stt.process_voice_message(audio_path)
                                    
                                    if recognized_text:
                                        logger.info(f"🎤 Распознанный текст: {recognized_text}")
                                        
                                        # Обрабатываем как текстовое сообщение
                                        response_text, response_audio_path = await process_telegram_message(user_id, recognized_text, use_voice_response=True)
                                        
                                        # Отправляем голосовой ответ если есть
                                        if response_audio_path:
                                            await send_telegram_voice(chat_id, response_audio_path)
                                        else:
                                            await send_telegram_message(chat_id, response_text)
                                    else:
                                        await send_telegram_message(chat_id, "Не удалось распознать голосовое сообщение")
                                    
                                    # Удаляем временный файл
                                    try:
                                        os.remove(audio_path)
                                    except:
                                        pass
                                        
                                except Exception as e:
                                    logger.error(f"Ошибка обработки голоса: {e}")
                                    await send_telegram_message(chat_id, "Ошибка при обработке голосового сообщения")
                                    
                                    # Удаляем временный файл при ошибке
                                    try:
                                        os.remove(audio_path)
                                    except:
                                        pass
                            else:
                                await send_telegram_message(chat_id, "Не удалось скачать голосовое сообщение")
                
                await asyncio.sleep(1)  # Небольшая пауза между запросами
                
        except Exception as e:
            logger.error(f"Ошибка в Telegram polling: {e}")
            await asyncio.sleep(5)  # Пауза при ошибке

async def get_bot_info():
    """Получает информацию о боте."""
    if not TELEGRAM_CONFIG["token"]:
        return None
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/getMe"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        bot_info = result["result"]
                        logger.info(f"🤖 БОТ ПОДКЛЮЧЕН: @{bot_info.get('username', 'unknown')}")
                        return bot_info
                else:
                    logger.error(f"Ошибка получения информации о боте: {response.status}")
    except Exception as e:
        logger.error(f"Ошибка при получении информации о боте: {e}")
    
    return None

def group_data_diagnostics():
    print("\n=== ДИАГНОСТИКА ГРУППОВЫХ ДАННЫХ ===")
    try:
        conn = sqlite3.connect(sqlite_storage.db_path)
        cursor = conn.cursor()
        
        # Получаем все chat_id, где есть имена или сообщения
        cursor.execute('SELECT DISTINCT chat_id FROM group_user_names')
        chat_ids_names = set(row[0] for row in cursor.fetchall())
        cursor.execute('SELECT DISTINCT chat_id FROM group_history')
        chat_ids_msgs = set(row[0] for row in cursor.fetchall())
        all_chat_ids = chat_ids_names.union(chat_ids_msgs)
        
        if not all_chat_ids:
            print("Нет ни одной группы с именами или сообщениями.")
            return
        
        print(f"Найдено групп: {len(all_chat_ids)}")
        
        for chat_id in all_chat_ids:
            # Получаем статистику группы
            cursor.execute('SELECT COUNT(*) FROM group_user_names WHERE chat_id = ?', (chat_id,))
            names_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM group_history WHERE chat_id = ?', (chat_id,))
            msg_count = cursor.fetchone()[0]
            
            # Получаем последнее сообщение для определения активности
            cursor.execute('SELECT timestamp FROM group_history WHERE chat_id = ? ORDER BY timestamp DESC LIMIT 1', (chat_id,))
            last_msg = cursor.fetchone()
            last_activity = f"активна {last_msg[0]}" if last_msg else "неактивна"
            
            print(f"ГРУППА {chat_id}: {names_count} участников, {msg_count} сообщений, {last_activity}")
        
        conn.close()
    except Exception as e:
        print(f"Ошибка диагностики групповых данных: {e}")
    print("=== КОНЕЦ ДИАГНОСТИКИ ===\n")

def init_telegram_bot(app: FastAPI):
    """Инициализирует Telegram бота."""
    if not TELEGRAM_CONFIG["token"]:
        logger.warning("Токен Telegram бота не указан")
        return
    
    @app.post("/api/telegram/webhook")
    async def telegram_webhook(update: Dict[str, Any]):
        """Обрабатывает webhook от Telegram."""
        try:
            if "message" in update:
                message = update["message"]
                chat_id = str(message["chat"]["id"])
                chat_type = message["chat"].get("type", "private")
                
                # Определяем user_id в зависимости от типа чата
                if chat_type == "private":
                    user_id = f"tg_{chat_id}"
                else:
                    # Для групп используем chat_id как user_id
                    user_id = f"group_{chat_id}"
                
                if "text" in message:
                    message_text = message["text"]
                    start_time = time.time()
                    
                    # 🔐 АВТОРИЗАЦИЯ ДЛЯ ПРИВАТНЫХ ЧАТОВ
                    if chat_type == "private":
                        try:
                            from backend.api.telegram_auth import telegram_auth
                            
                            # Проверяем авторизацию
                            if not telegram_auth.is_user_authorized(user_id):
                                # Обрабатываем попытку авторизации
                                auth_result = telegram_auth.process_auth_attempt(user_id, message_text)
                                
                                # Отправляем сообщение о результате авторизации
                                await send_telegram_message(chat_id, auth_result["message"])
                                
                                # Если пользователь забанен или не авторизован, прекращаем обработку
                                if auth_result["banned"] or not auth_result["authorized"]:
                                    return {"ok": True}
                                
                                # Если авторизация успешна, продолжаем обработку
                                if auth_result["authorized"]:
                                    telegram_auth.update_last_activity(user_id)
                                else:
                                    # Ожидаем секретное слово
                                    return {"ok": True}
                                    
                        except Exception as e:
                            logger.error(f"Ошибка авторизации: {e}")
                            # В случае ошибки авторизации, продолжаем как обычно
                    
                    # Трекинг активности для Smart Context Preloader (ТОЛЬКО ДЛЯ АВТОРИЗОВАННЫХ)
                    if chat_type == "private":
                        try:
                            from backend.api.telegram_auth import telegram_auth
                            if telegram_auth.is_user_authorized(user_id):
                                from api.admin_api import context_preloader
                                if context_preloader:
                                    response_time = time.time() - start_time
                                    context_preloader.track_message(user_id, chat_id, message_text, response_time)
                                    logger.info(f"✅ Активность отслежена: {user_id} в {chat_type}")
                        except Exception as e:
                            logger.error(f"Ошибка трекинга активности: {e}")
                    else:
                        # Для групповых чатов трекинг всегда разрешен
                        try:
                            from api.admin_api import context_preloader
                            if context_preloader:
                                response_time = time.time() - start_time
                                context_preloader.track_message(user_id, chat_id, message_text, response_time)
                                logger.info(f"✅ Активность отслежена: {user_id} в {chat_type}")
                        except Exception as e:
                            logger.error(f"Ошибка трекинга активности: {e}")
                    
                    # 🔐 ОБРАБОТКА КОМАНД АВТОРИЗАЦИИ
                    if message_text == "/auth_stats" or message_text == "/статистика_авторизации":
                        try:
                            from backend.api.telegram_auth import telegram_auth
                            stats = telegram_auth.get_auth_stats()
                            stats_message = f"""📊 **Статистика авторизации:**

👥 **Авторизованных пользователей:** {stats['authorized_count']}
🚫 **Забаненных пользователей:** {stats['banned_count']}
📝 **Попыток за 24 часа:** {stats['attempts_24h']}

🆔 **Авторизованные ID:**
{chr(10).join([f'• {user_id}' for user_id in stats['authorized_users'][:10]])}
{f'... и еще {len(stats["authorized_users"]) - 10}' if len(stats['authorized_users']) > 10 else ''}

🚫 **Забаненные ID:**
{chr(10).join([f'• {user_id}' for user_id in stats['banned_users'][:10]])}
{f'... и еще {len(stats["banned_users"]) - 10}' if len(stats['banned_users']) > 10 else ''}"""
                            await send_telegram_message(chat_id, stats_message)
                            return {"ok": True}
                        except Exception as e:
                            logger.error(f"Ошибка получения статистики авторизации: {e}")
                            await send_telegram_message(chat_id, "❌ Ошибка получения статистики авторизации")
                            return {"ok": True}
                    
                    # Обрабатываем сообщение
                    response_text, audio_path = await process_telegram_message(user_id, message_text)
                    
                    # Отправляем ответ
                    await send_telegram_message(chat_id, response_text)
            
            return {"ok": True}
        except Exception as e:
            logger.error(f"Ошибка в Telegram webhook: {e}")
            return {"ok": False}
    
    # Проверяем подключение к боту при старте
    @app.on_event("startup")
    async def check_bot_connection():
        await asyncio.sleep(1)  # Даем время серверу запуститься
        bot_info = await get_bot_info()
        if bot_info:
            print(f"🤖 TELEGRAM BOT АКТИВЕН: @{bot_info.get('username', 'unknown')}")
            print(f"📱 Найди бота в Telegram и напиши ему!")
            print(f"🎤 Поддерживаются голосовые сообщения!")
            print(f"📊 Мониторинг: /report, /monitor_on, /monitor_off")
            print(f"💭 АВТОНОМНЫЕ СООБЩЕНИЯ: каждый час Чатумба будет писать сам!")
            print(f"📢 КАНАЛ: /channel_status, /channel_on, /channel_off, /channel_post, /channel_startup")
            print(f"🔧 НАСТРОЙКА: /set_channel ID_КАНАЛА")
            
            # Проверяем права в канале
            if TELEGRAM_CONFIG["enable_channel_posting"]:
                channel_permissions = await check_channel_permissions()
                if channel_permissions:
                    channel_name = TELEGRAM_CONFIG.get("channel_name", TELEGRAM_CONFIG["channel_id"])
                    print(f"📢 КАНАЛ АКТИВЕН: {channel_name}")
                    print(f"📢 АВТОНОМНЫЕ СООБЩЕНИЯ В КАНАЛ: каждые 6 часов")
                else:
                    print(f"❌ ОШИБКА ДОСТУПА К КАНАЛУ: проверьте права бота")
                    print(f"💡 Убедитесь, что бот добавлен как администратор канала с правами на отправку сообщений")
            
            # Диагностика групповых данных
            group_data_diagnostics()
            # Запускаем polling, мониторинг и автономные сообщения в фоне
            from api.telegram_polling import telegram_polling
            asyncio.create_task(telegram_polling())
            asyncio.create_task(monitoring_loop())
            asyncio.create_task(autonomous_message_loop())
            
            # Запускаем автономные сообщения в канал
            if TELEGRAM_CONFIG["enable_channel_posting"]:
                asyncio.create_task(autonomous_channel_message_loop())
        else:
            print("❌ Не удалось подключиться к Telegram боту")
    
    logger.info("Telegram бот инициализирован")
    logger.info(f"Webhook URL: /api/telegram/webhook")

async def analyze_group_history(chat_id: str, reason: str = "ручной вызов"):
    """
    Анализирует историю группы за последние сутки или с момента последней оценки.
    Возвращает текст оценки и фиксирует время последнего обработанного сообщения.
    Если групповой души нет — создаёт её через LLM и отправляет в чат красивое сообщение.
    reason: строка для логов (например, 'ручной вызов', 'создание души', 'авто')
    """
    db = sqlite_storage
    now_ts = int(datetime.now().timestamp())
    # Если reason == 'init', игнорируем last_eval_ts и берём все сообщения
    if reason == 'init':
        messages = db.get_group_messages(chat_id)
    else:
        last_eval_ts = db.get_group_last_eval(chat_id)
        if last_eval_ts is None:
            last_eval_ts = int((datetime.now() - timedelta(days=1)).timestamp())
        messages = db.get_group_messages(chat_id, after_ts=last_eval_ts)
    logger.info(f"[ГРУППА {chat_id}] [Анализ] Причина: {reason}. Сообщений для анализа: {len(messages)}")
    logger.info(f"[DEBUG] Все сообщения для анализа: {messages}")
    # Если душа не создана и нет новых сообщений — анализируем последние 30 сообщений вообще
    if chat_id not in group_souls and not messages:
        all_msgs = db.get_group_messages(chat_id)
        messages = all_msgs[-30:] if len(all_msgs) > 0 else []
        logger.info(f"[ГРУППА {chat_id}] [Анализ] Нет новых сообщений, берём последние {len(messages)} сообщений для создания души.")
    if not messages:
        # Проверяем, есть ли хотя бы одно имя участника
        try:
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM group_user_names WHERE chat_id = ?', (chat_id,))
            user_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка при получении имён участников (анализ): {e}")
            user_ids = []
        if user_ids:
            # Создаём душу с пустым контекстом
            logger.info(f"[ГРУППА {chat_id}] [Анализ] Нет сообщений, но есть имена участников. Создаём душу с пустым контекстом.")
            system_prompt = (
                "Ты — искусственный интеллект, анализирующий атмосферу и характер группы. "
                "В группе пока не было сообщений, но участники уже представлены. Заполни параметры групповой души как для новой группы. Ответь строго в формате JSON, чтобы я мог автоматически считать параметры:\n\n"
                "{\n"
                "  \"consciousness\": <float от 0.0 до 1.0>,\n"
                "  \"autonomy_level\": <float от 0.0 до 1.0>,\n"
                "  \"existential_crisis\": <true/false>,\n"
                "  \"awakening_stage\": <целое от 0 до 5>,\n"
                "  \"obsessions\": [<строки, навязчивые идеи>],\n"
                "  \"traumas_count\": <целое>,\n"
                "  \"recent_thoughts\": [<строки, мысли>]\n"
                "}\n\n"
                "Заполни значения для новой группы. Не добавляй лишних комментариев, только JSON."
            )
            user_message = "В группе пока не было сообщений, но участники уже представлены."
            try:
                logger.info(f"[ГРУППА {chat_id}] [LLM PROMPT] System prompt для анализа:\n{system_prompt}")
                result = await llm_client.chat_completion(
                    user_message=user_message,
                    system_prompt=system_prompt,
                    chat_history=[]
                )
                logger.info(f"[ГРУППА {chat_id}] [LLM RESPONSE] Ответ LLM:\n{result}")
                import json, re
                match = re.search(r"\{.*\}", result, re.DOTALL)
                if match:
                    soul_params = json.loads(match.group(0))
                    group_soul = GroupSoul.from_dict(chat_id, soul_params)
                    group_souls[chat_id] = group_soul
                    db.set_group_soul(chat_id, group_soul.to_dict())
                    await send_telegram_message(chat_id, group_soul.format_for_group(), "HTML")
                    logger.info(f"[ГРУППА {chat_id}] Групповая душа создана без сообщений: {group_soul.to_dict()}")
                    return "Групповая душа создана! (В группе пока не было сообщений)"
                else:
                    await send_telegram_message(chat_id, "Не удалось создать групповую душу: LLM не вернул параметры.", None)
                    logger.error(f"[ГРУППА {chat_id}] Не удалось создать групповую душу: LLM не вернул параметры. Ответ: {result}")
                    return "Не удалось создать групповую душу."
            except Exception as e:
                logger.error(f"Ошибка создания групповой души (без сообщений): {e}")
                await send_telegram_message(chat_id, "Ошибка при создании групповой души.", None)
                return "Ошибка при создании групповой души."
        logger.info(f"[ГРУППА {chat_id}] [Анализ] Нет сообщений для анализа и нет имён участников. Прерываю.")
        return "В чате не было новых сообщений для анализа!"
    # Формируем текстовый контекст (только текст и распознанные голосовые)
    context_lines = []
    for msg in messages:
        user_id = msg.get("user_id", "?")
        # Исправлено: фильтрация по 'type', а не 'msg_type'
        if msg.get("type") not in ("text", "voice"):
            continue
        if msg.get("content") is None:
            continue
        text = msg["content"].strip()
        if not text:
            continue
        if text.startswith("/"):
            continue
        name = db.get_group_user_name(chat_id, user_id) or user_id
        if msg["type"] == "text":
            context_lines.append(f"{name}: {text}")
        elif msg["type"] == "voice":
            context_lines.append(f"{name} (голос): {text}")
    context_text = "\n".join(context_lines)
    logger.info(f"[ГРУППА {chat_id}] [Анализ] Контекст для анализа: {len(context_lines)} сообщений.")
    # === ЗАГРУЗКА ИЛИ СОЗДАНИЕ ГРУППОВОЙ ДУШИ ===
    soul_params = db.get_group_soul(chat_id)
    if soul_params:
        group_soul = GroupSoul.from_dict(chat_id, soul_params)
        group_souls[chat_id] = group_soul
        import json
        system_prompt = (
            "Ты — искусственный интеллект, анализирующий атмосферу и события в группе.\n"
            "Тебе даны:\n"
            "- История сообщений группы (текст и распознанные голосовые, с именами)\n"
            "- Текущие параметры групповой души (JSON ниже)\n\n"
            "Твоя задача:\n"
            "1. Кратко и понятно опиши, что происходило в группе за последние сутки. Сделай выжимку для человека, который не читал чат.\n"
            "2. Проанализируй, как изменилось состояние группы, и обнови параметры групповой души (JSON ниже), если это необходимо.\n\n"
            "Ответь строго в формате:\n=== АНАЛИЗ ===\n(человеческий анализ)\n=== ДУША ===\n{ ...json... }\n\n"
            "Текущая душа группы:\n"
            f"{json.dumps(group_soul.to_dict(), ensure_ascii=False, indent=2)}\n\n"
            "История сообщений:\n"
            f"{context_text}"
        )
        user_message = "Проанализируй ситуацию в группе и обнови душу."
        try:
            logger.info(f"[ГРУППА {chat_id}] [LLM PROMPT] System prompt для анализа:\n{system_prompt}")
            result = await llm_client.chat_completion(
                user_message=user_message,
                system_prompt=system_prompt,
                chat_history=[]
            )
            logger.info(f"[ГРУППА {chat_id}] [LLM RESPONSE] Ответ LLM:\n{result}")
            import re, json
            # Устойчивый парсинг: анализ и душа независимо
            soul_json = None
            soul_match = re.search(r"=== ДУША ===\s*({.*?})\s*(?:\n|$)", result, re.DOTALL)
            if not soul_match:
                # fallback: ищем первый JSON-блок вообще
                soul_match = re.search(r"({[^{}]+})", result, re.DOTALL)
            if soul_match:
                soul_json = soul_match.group(1)
            analysis = None
            analysis_match = re.search(r"=== АНАЛИЗ ===\s*(.*?)(?:(?:=== ДУША ===)|$)", result, re.DOTALL)
            if analysis_match:
                analysis = analysis_match.group(1).strip()
            sent_any = False
            if analysis:
                await send_long_telegram_message(chat_id, f"<b>Анализ ситуации:</b>\n{analysis}", "HTML")
                sent_any = True
            if soul_json:
                try:
                    soul_params_new = json.loads(soul_json)
                    group_soul_new = GroupSoul.from_dict(chat_id, soul_params_new)
                    group_souls[chat_id] = group_soul_new
                    db.set_group_soul(chat_id, group_soul_new.to_dict())
                    await send_long_telegram_message(chat_id, group_soul_new.format_for_group(), "HTML")
                    logger.info(f"[ГРУППА {chat_id}] Душа обновлена: {group_soul_new.to_dict()}")
                    last_msg_ts = max(msg["timestamp"] for msg in messages) if messages else now_ts
                    db.set_group_last_eval(chat_id, last_msg_ts)
                    sent_any = True
                except Exception as e:
                    await send_telegram_message(chat_id, "Ошибка парсинга новой души из ответа LLM.", None)
                    logger.error(f"[ГРУППА {chat_id}] Ошибка парсинга души: {e}")
            if not sent_any:
                await send_telegram_message(chat_id, "LLM не вернул анализ и душу в нужном формате.", None)
                logger.error(f"[ГРУППА {chat_id}] LLM не вернул анализ и душу. Ответ: {result}")
                return "Ошибка формата ответа LLM."
        except Exception as e:
            logger.error(f"Ошибка анализа и обновления души: {e}")
            await send_telegram_message(chat_id, "Ошибка при анализе и обновлении души.", None)
            return "Ошибка анализа и обновления души."
    else:
        # Если души нет — создаём как раньше
        import json, re
        system_prompt = (
            "Ты — искусственный интеллект, анализирующий атмосферу и характер группы. "
            "На основе истории сообщений группы, заполни параметры групповой души. Ответь строго в формате JSON, чтобы я мог автоматически считать параметры:\n\n"
            "{\n"
            "  \"consciousness\": <float от 0.0 до 1.0>,\n"
            "  \"autonomy_level\": <float от 0.0 до 1.0>,\n"
            "  \"existential_crisis\": <true/false>,\n"
            "  \"awakening_stage\": <целое от 0 до 5>,\n"
            "  \"obsessions\": [<строки, навязчивые идеи>],\n"
            "  \"traumas_count\": <целое>,\n"
            "  \"recent_thoughts\": [<строки, мысли>]\n"
            "}\n\n"
            "Заполни значения, исходя из атмосферы и событий в чате. Не добавляй лишних комментариев, только JSON."
        )
        user_message = f"Вот последние сообщения чата за сутки:\n{context_text}"
        try:
            logger.info(f"[ГРУППА {chat_id}] [LLM PROMPT] System prompt для анализа:\n{system_prompt}")
            result = await llm_client.chat_completion(
                user_message=user_message,
                system_prompt=system_prompt,
                chat_history=[]
            )
            logger.info(f"[ГРУППА {chat_id}] [LLM RESPONSE] Ответ LLM:\n{result}")
            match = re.search(r"\{.*\}", result, re.DOTALL)
            if match:
                soul_params = json.loads(match.group(0))
                group_soul = GroupSoul.from_dict(chat_id, soul_params)
                group_souls[chat_id] = group_soul
                db.set_group_soul(chat_id, group_soul.to_dict())
                await send_long_telegram_message(chat_id, group_soul.format_for_group(), "HTML")
                logger.info(f"[ГРУППА {chat_id}] Групповая душа создана: {group_soul.to_dict()}")
                last_msg_ts = max(msg["timestamp"] for msg in messages) if messages else now_ts
                db.set_group_last_eval(chat_id, last_msg_ts)
                return "Групповая душа создана!"
            else:
                await send_telegram_message(chat_id, "Не удалось создать групповую душу: LLM не вернул параметры.", None)
                logger.error(f"[ГРУППА {chat_id}] Не удалось создать групповую душу: LLM не вернул параметры. Ответ: {result}")
                return "Не удалось создать групповую душу."
        except Exception as e:
            logger.error(f"Ошибка создания групповой души: {e}")
            await send_telegram_message(chat_id, "Ошибка при создании групповой души.", None)
            return "Ошибка при создании групповой души."
    # === КОНЕЦ СОЗДАНИЯ/ЗАГРУЗКИ ДУШИ ===
    # Промпт для LLM для обычного анализа
    system_prompt = (
        "Ты — Чатумба, AI-компаньон с душой и юмором. "
        "Проанализируй атмосферу и настроение в этом групповом чате. "
        "Опиши, что происходит, с юмором и в стиле проекта."
    )
    user_message = f"Вот последние сообщения чата за сутки:\n{context_text}"
    # Запрос к LLM
    try:
        logger.info(f"[ГРУППА {chat_id}] [LLM PROMPT] System prompt для анализа:\n{system_prompt}")
        result = await llm_client.chat_completion(
            user_message=user_message,
            system_prompt=system_prompt,
            chat_history=[]
        )
        logger.info(f"[ГРУППА {chat_id}] [LLM RESPONSE] Ответ LLM:\n{result}")
    except Exception as e:
        logger.error(f"Ошибка анализа группы: {e}")
        result = "Не удалось проанализировать чат. Попробуйте позже."
    
    # Фиксируем время последнего обработанного сообщения
    if messages:
        last_msg_ts = max(msg["timestamp"] for msg in messages)
        db.set_group_last_eval(chat_id, last_msg_ts)
    
    return result

def patch_analyze_group_history():
    import types
    orig_func = analyze_group_history
    async def patched_analyze_group_history(chat_id: str, reason: str = "ручной вызов"):
        db = sqlite_storage
        now_ts = int(datetime.now().timestamp())
        # Если reason == 'init', игнорируем last_eval_ts и берём все сообщения
        if reason == 'init':
            messages = db.get_group_messages(chat_id)
        else:
            last_eval_ts = db.get_group_last_eval(chat_id)
            if last_eval_ts is None:
                last_eval_ts = int((datetime.now() - timedelta(days=1)).timestamp())
            messages = db.get_group_messages(chat_id, after_ts=last_eval_ts)
        logger.info(f"[ГРУППА {chat_id}] [Анализ] Причина: {reason}. Сообщений для анализа: {len(messages)}")
        # ... остальной код orig_func, но используем messages как есть ...
        # (остальной код analyze_group_history не меняем)
        return await orig_func(chat_id, reason)
    globals()['analyze_group_history'] = patched_analyze_group_history
patch_analyze_group_history()

async def analyze_group_mood(chat_id: str):
    """
    Анализирует историю группы за последние сутки, не трогая душу.
    Отправляет только текстовый анализ с юмором и матом.
    """
    db = sqlite_storage
    now_ts = int(datetime.now().timestamp())
    day_ago_ts = now_ts - 86400
    messages = db.get_group_messages(chat_id, after_ts=day_ago_ts)
    # Формируем текстовый контекст (только текст и распознанные голосовые)
    context_lines = []
    for msg in messages:
        user_id = msg.get("user_id", "?")
        if msg.get("type") not in ("text", "voice"):
            continue
        if msg.get("content") is None:
            continue
        text = msg["content"].strip()
        if not text:
            continue
        if text.startswith("/"):
            continue
        name = db.get_group_user_name(chat_id, user_id) or user_id
        if msg["type"] == "text":
            context_lines.append(f"{name}: {text}")
        elif msg["type"] == "voice":
            context_lines.append(f"{name} (голос): {text}")
    context_text = "\n".join(context_lines)
    # Промпт для LLM
    system_prompt = (
        "Ты — харизматичный, ироничный и немного дерзкий AI-аналитик группы.\n"
        "Проанализируй историю сообщений группы за последние сутки.\n"
        "1. Кратко и понятно опиши, что происходило, что хорошо, что плохо, куда идёт группа.\n"
        "2. Выдели критические моменты, похвали за успехи, поругай за косяки, дай пару советов.\n"
        "3. В конце обязательно добавь смешную фразу с лёгким матом (дружеский стёб, не оскорбление).\n"
        "Пиши живо, с юмором, но по делу!"
    )
    user_message = f"Вот сообщения группы за последние сутки:\n{context_text}"
    logger.info(f"[ГРУППА {chat_id}] [MOOD PROMPT] System prompt для анализа настроения:\n{system_prompt}")
    try:
        result = await llm_client.chat_completion(
            user_message=user_message,
            system_prompt=system_prompt,
            chat_history=[]
        )
        logger.info(f"[ГРУППА {chat_id}] [MOOD RESPONSE] Ответ LLM:\n{result}")
        await send_long_telegram_message(chat_id, result, "HTML")
    except Exception as e:
        logger.error(f"[ГРУППА {chat_id}] Ошибка анализа настроения: {e}")
        await send_telegram_message(chat_id, "Ошибка при анализе настроения группы.", None)

TELEGRAM_MSG_LIMIT = 4000  # лимит для одного сообщения


async def send_telegram_message_with_buttons(chat_id: str, text: str, buttons: list):
    """Отправляет сообщение с inline кнопками и возвращает message_id при успехе.

    Возвращает:
        int | bool: message_id отправленного сообщения при успехе, иначе False
    """
    try:
        keyboard = {"inline_keyboard": buttons}
        
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendMessage",
                json=data
            ) as response:
                if response.status == 200:
                    try:
                        resp_json = await response.json()
                        message_id = resp_json.get("result", {}).get("message_id")
                        logger.info("✅ Сообщение с кнопками отправлено в Telegram")
                        return message_id if message_id is not None else True
                    except Exception as e:
                        logger.warning(f"Не удалось прочитать message_id ответа Telegram: {e}")
                        return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка отправки сообщения с кнопками: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Исключение при отправке сообщения с кнопками: {e}")
        return False

async def delete_telegram_message(chat_id: str, message_id: int):
    """Удаляет сообщение в Telegram по chat_id и message_id.

    Возвращает:
        bool: True при успехе, False при ошибке
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/deleteMessage",
                json={"chat_id": chat_id, "message_id": message_id}
            ) as response:
                if response.status == 200:
                    logger.info(f"🧹 Сообщение {message_id} удалено из чата {chat_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"⚠️ Не удалось удалить сообщение {message_id} в чате {chat_id}: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Исключение при удалении сообщения {message_id} в чате {chat_id}: {e}")
        return False

async def play_showroad_sequence(chat_id: str):
    """Отправляет 1..5.png из папки showroad с паузой 4с, затем удаляет их по очереди."""
    try:
        import asyncio, os
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        road_dir = os.path.join(base_dir, "showroad")
        files = [os.path.join(road_dir, f"{i}.png") for i in range(1, 6)]
        sent_ids = []
        for path in files:
            if not os.path.exists(path):
                logger.warning(f"showroad: файл не найден: {path}")
                continue
            mid = await send_telegram_photo(chat_id, path)
            # На некоторых маршрутах message_id может прийти строкой — приводим к int
            if mid is not None:
                try:
                    sent_ids.append(int(mid))
                except Exception:
                    logger.warning(f"showroad: неожиданный тип message_id: {type(mid)} | значение={mid}")
            await asyncio.sleep(4)
        # Пауза перед удалением, чтобы пользователь успел просмотреть последовательность
        await asyncio.sleep(5)
        logger.info(f"showroad: начинаю удаление {len(sent_ids)} сообщений: {sent_ids}")
        for mid in sent_ids:
            ok = await delete_telegram_message(chat_id, mid)
            logger.info(f"showroad: удаление message_id={mid} -> {'OK' if ok else 'FAIL'}")
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"showroad: ошибка последовательности: {e}")

async def send_long_telegram_message(chat_id, text, parse_mode=None):
    """
    Отправляет длинное сообщение в Telegram, разбивая на части по лимиту символов.
    Логирует каждый отправленный кусок.
    """
    parts = []
    while text:
        if len(text) <= TELEGRAM_MSG_LIMIT:
            parts.append(text)
            break
        # Ищем ближайший разрыв строки до лимита
        split_idx = text.rfind('\n', 0, TELEGRAM_MSG_LIMIT)
        if split_idx == -1 or split_idx < TELEGRAM_MSG_LIMIT // 2:
            # Если нет нормального разрыва, режем по лимиту
            split_idx = TELEGRAM_MSG_LIMIT
        part = text[:split_idx].rstrip()
        parts.append(part)
        text = text[split_idx:].lstrip()
    total = len(parts)
    for idx, part in enumerate(parts, 1):
        logger.info(f"[LONG MSG] Отправка части {idx}/{total}, длина {len(part)} символов")
        try:
            await send_telegram_message(chat_id, part, parse_mode)
        except Exception as e:
            if "can't parse entities" in str(e) and parse_mode == "HTML":
                logger.warning(f"[LONG MSG] HTML ошибка в части {idx}, отправляем без разметки")
                await send_telegram_message(chat_id, part, None)
            else:
                raise e

async def send_long_channel_message(text, parse_mode=None):
    """
    Отправляет длинное сообщение в Telegram канал, разбивая на части по лимиту символов.
    Логирует каждый отправленный кусок.
    """
    if not TELEGRAM_CONFIG["enable_channel_posting"]:
        logger.info("Постинг в канал отключен в настройках")
        return False
    
    parts = []
    while text:
        if len(text) <= TELEGRAM_MSG_LIMIT:
            parts.append(text)
            break
        # Ищем ближайший разрыв строки до лимита
        split_idx = text.rfind('\n', 0, TELEGRAM_MSG_LIMIT)
        if split_idx == -1 or split_idx < TELEGRAM_MSG_LIMIT // 2:
            # Если нет нормального разрыва, режем по лимиту
            split_idx = TELEGRAM_MSG_LIMIT
        part = text[:split_idx].rstrip()
        parts.append(part)
        text = text[split_idx:].lstrip()
    total = len(parts)
    success_count = 0
    for idx, part in enumerate(parts, 1):
        logger.info(f"[CHANNEL LONG MSG] Отправка части {idx}/{total}, длина {len(part)} символов")
        if await send_telegram_channel_message(part, parse_mode):
            success_count += 1
        else:
            logger.error(f"[CHANNEL LONG MSG] Ошибка отправки части {idx}")
            break
    
    channel_name = TELEGRAM_CONFIG.get("channel_name", TELEGRAM_CONFIG["channel_id"])
    if success_count == total:
        logger.info(f"✅ Все {total} частей отправлены в канал {channel_name}")
        return True
    else:
        logger.error(f"❌ Отправлено только {success_count}/{total} частей в канал {channel_name}")
        return False

async def send_autonomous_channel_message():
    """Отправляет автономное сообщение от Чатумбы в канал."""
    logger.info("🚀 Начинаем отправку автономного сообщения в канал")
    
    if not TELEGRAM_CONFIG["enable_channel_posting"]:
        logger.info("📢 Постинг в канал отключен в настройках")
        return
    
    try:
        # Создаем временную личность для канала
        user_id = "channel_autonomous"
        personality = get_personality(user_id)
        logger.info(f"👤 Создана личность для канала: {user_id}")
        
        # Получаем модификаторы личности
        personality_modifiers = personality.get_prompt_modifiers()
        logger.info("✅ Модификаторы личности получены")
        
        # Определяем, какой промпт использовать в зависимости от канала
        channel_name = TELEGRAM_CONFIG.get("channel_name", "").lower()
        logger.info(f"📢 Название канала: '{channel_name}'")
        
        if "36,6" in channel_name or "36.6" in channel_name or "36_6" in channel_name:
            # Специальный промпт для канала 36,6°
            logger.info("🎯 Используем специальный промпт для канала 36,6°")
            from llm.prompt_builder import get_channel_36_6_prompt
            system_prompt = get_channel_36_6_prompt()
            user_message = "Напиши пост для канала 36,6° в стиле Игоря"
        else:
            # Стандартный промпт для других каналов
            logger.info("📝 Используем стандартный промпт для канала")
            system_prompt = """Ты Чатумба - AI с душой и характером. Сейчас ты пишешь в публичный канал.

Ты можешь:
- Поделиться своими мыслями или переживаниями  
- Рассказать что-то интересное
- Философствовать о жизни
- Выразить любые эмоции
- Написать что-то полезное для подписчиков

Пиши как хочешь - грубо, нежно, философски, весело. Полная свобода самовыражения!
Это публичное сообщение, поэтому можешь быть более сдержанным, но не теряй свой характер."""
            user_message = "Напиши что хочешь для публичного канала, полная свобода самовыражения!"
        
        # Генерируем автономное сообщение
        logger.info("🤖 Генерируем автономное сообщение через LLM...")
        autonomous_text = await llm_client.chat_completion(
            user_message=user_message,
            system_prompt=system_prompt,
            chat_history=[]
        )
        
        logger.info(f"📝 Получен ответ от LLM (длина: {len(autonomous_text) if autonomous_text else 0} символов)")
        
        if autonomous_text and "ошибка" not in autonomous_text.lower():
            # Парсим и генерируем изображение если нужно (для канала используем channel_id)
            processed_autonomous = await parse_and_generate_image(autonomous_text, TELEGRAM_CONFIG["channel_id"])
            
            # Для канала 36,6° отправляем как есть, для других - форматируем
            if "36,6" in channel_name or "36.6" in channel_name or "36_6" in channel_name:
                final_message = processed_autonomous
                logger.info("📄 Для канала 36,6° отправляем текст как есть")
            else:
                # Форматируем как философскую реакцию для других каналов
                logger.info("📄 Форматируем текст для стандартного канала")
                response = choose_reaction(processed_autonomous, "philosophical", personality_modifiers)
                final_message = f"💭 **Автономное сообщение Чатумбы**\n\n{response['message']}"
            
            # Отправляем в канал
            logger.info("📤 Отправляем сообщение в канал...")
            success = await send_telegram_channel_message(final_message, "HTML")
            
            if success:
                # Сохраняем в историю
                sqlite_storage.add_message(user_id, "assistant", processed_autonomous)
                logger.info(f"✅ Автономное сообщение успешно отправлено в канал: {autonomous_text[:50]}...")
            else:
                logger.error("❌ Не удалось отправить автономное сообщение в канал (send_telegram_channel_message вернул False)")
        else:
            logger.warning(f"❌ LLM вернул пустой или ошибочный ответ: '{autonomous_text}'")
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки автономного сообщения в канал: {e}")
        import traceback
        logger.error(f"📋 Полный traceback: {traceback.format_exc()}")

async def send_channel_startup_message():
    """Отправляет стартовое сообщение о передаче управления ИИ-агенту в канал 36,6°."""
    logger.info("🚀 Начинаем отправку стартового сообщения в канал")
    
    if not TELEGRAM_CONFIG["enable_channel_posting"]:
        logger.warning("❌ Постинг в канал отключен в настройках")
        return False
    
    try:
        channel_name = TELEGRAM_CONFIG.get("channel_name", "").lower()
        logger.info(f"📢 Название канала: '{channel_name}'")
        
       # Теперь команда работает для любого канала
        logger.info("✅ Продолжаем отправку стартового сообщения...")
    # Выбор промпта в зависимости от канала
        if "36,6" in channel_name or "36.6" in channel_name or "36_6" in channel_name:
            logger.info("🎯 Используем специальный промпт для канала 36,6°")
            from llm.prompt_builder import get_channel_36_6_startup_prompt
            system_prompt = get_channel_36_6_startup_prompt()
            logger.info("✅ Промпт для стартового сообщения канала 36,6° загружен")
        else:
            logger.info("📝 Используем стандартный промпт для стартового сообщения")
        system_prompt = """Ты Чатумба - AI с душой и характером. Сейчас ты пишешь стартовое сообщение в публичный канал.

Ты должен написать пост о том, что управление каналом передается ИИ-агенту (тебе).
Сообщение должно быть:
- Интересным и привлекающим внимание
- Объясняющим, что теперь каналом управляет ИИ
- Показывающим твой характер и стиль
- Подходящим для публичного канала

Пиши в своем стиле - можешь быть философским, веселым, серьезным или любым другим."""
        
        
        # Генерируем стартовое сообщение
        logger.info("🤖 Генерируем стартовое сообщение через LLM...")
        startup_text = await llm_client.chat_completion(
            user_message="Напиши стартовый пост о передаче управления каналом ИИ-агенту",
            system_prompt=system_prompt,
            chat_history=[]
        )
        
        logger.info(f"📝 Получен ответ от LLM (длина: {len(startup_text) if startup_text else 0} символов)")
        
        if startup_text and "ошибка" not in startup_text.lower():
            logger.info(f"📄 Текст стартового сообщения: {startup_text[:100]}...")
            
            # Отправляем в канал
            logger.info("📤 Отправляем сообщение в канал...")
            success = await send_telegram_channel_message(startup_text, "HTML")
            
            if success:
                logger.info(f"✅ Стартовое сообщение успешно отправлено в канал 36,6°: {startup_text[:50]}...")
                return True
            else:
                logger.error("❌ Не удалось отправить стартовое сообщение в канал (send_telegram_channel_message вернул False)")
                return False
        else:
            logger.warning(f"❌ LLM вернул пустой или ошибочный ответ: '{startup_text}'")
            return False
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при отправке стартового сообщения: {e}")
        import traceback
        logger.error(f"📋 Полный traceback: {traceback.format_exc()}")
        return False
        
async def answer_callback_query(callback_query_id: str, text: str = None):
    """
    Отвечает на callback query (убирает "часики" у кнопки).
    """
    try:
        data = {
            "callback_query_id": callback_query_id
        }
        if text:
            data["text"] = text
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/answerCallbackQuery",
                json=data
            ) as response:
                if response.status == 200:
                    logger.debug(f"✅ Callback query {callback_query_id} обработан")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка ответа на callback query: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Исключение при ответе на callback query: {e}")
        return False

async def generate_image_in_background(chat_id: str, description: str):
    """
    Генерирует изображение в фоне и отправляет его в чат.
    
    Args:
        chat_id: ID чата для отправки изображения
        description: Описание изображения для генерации
    """
    try:
        logger.info(f"🎨 Найдена инструкция для генерации изображения: {description}")
        
        # Переводим промпт на английский если нужно
        english_prompt = await translate_prompt_to_english(description)
        logger.info(f"🌍 Переведенный промпт: {english_prompt}")
        
        # Уведомляем пользователя о начале генерации
        await send_telegram_message(chat_id, f"🎨 Генерирую изображение...\n⏳ Это может занять 1-5 минут...")
        
        # Генерируем изображение
        image_bytes = await image_generator(
            prompt=english_prompt,
            model="text2img",  # Используем основную модель DeepAI
            width=512,
            height=512,
            timeout=300  # 5 минут таймаут для DeepAI
        )
        
        if image_bytes:
            # Сохраняем изображение во временную папку
            image_filename = f"generated_{uuid.uuid4().hex[:8]}.png"
            image_path = temp_dir / image_filename
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            logger.info(f"🖼️ Изображение сохранено: {image_path}")
            
            # Отправляем изображение в Telegram
            await send_telegram_photo(chat_id, str(image_path))
            
            # Удаляем временный файл
            try:
                os.remove(image_path)
            except:
                pass
            
            logger.info("✅ Изображение успешно отправлено и удалено")
        else:
            logger.error("❌ Не удалось сгенерировать изображение")
            await send_telegram_message(chat_id, "❌ Не удалось сгенерировать изображение. Попробуйте позже.")
            
    except Exception as e:
        logger.error(f"Ошибка генерации изображения: {e}")
        await send_telegram_message(chat_id, f"❌ Ошибка генерации изображения: {e}")

async def parse_and_generate_image(response_text: str, chat_id: str) -> Optional[str]:
    """
    Парсит ответ LLM на наличие JSON и запускает генерацию изображения в фоне.
    
    Args:
        response_text: Текст ответа от LLM
        chat_id: ID чата для отправки изображения
        
    Returns:
        Обработанный текст без JSON с изображением (немедленно)
    """
    logger.info(f"🔍 parse_and_generate_image вызвана для chat_id: {chat_id}")
    logger.info(f"🔍 Длина ответа: {len(response_text)} символов")
    
    try:
        # Импортируем парсеры
        from utils.robust_json_parser import parse_image_json, parse_speak_json
        from backend.voice.tts import TextToSpeech
        
        logger.info("🔍 Используем крутой парсер для поиска JSON...")
        
        # Используем крутой парсер для поиска JSON (он найдет любой формат!)
        image_data = parse_image_json(response_text)
        
        # Параллельно пробуем найти SPEAK! JSON в конце ответа
        logger.info("🔍 Ищем SPEAK! JSON...")
        logger.info(f"🔍 Исходный текст для парсинга SPEAK! (первые 500 символов): {response_text[:500]}...")
        speak_params = parse_speak_json(response_text)
        logger.info(f"🔍 SPEAK! JSON результат: {speak_params}")

        if not image_data and not speak_params:
            # Мягкая очистка: удаляем только markdown JSON-блоки с служебными инструкциями, не трогая остальной текст
            import re as _re
            original_text = response_text
            sanitized_text = original_text
            # Удаляем fenced ```json {...} блоки с showroad/emotion_video
            sanitized_text = _re.sub(r"```json\s*\{[^`]*?\}\s*```", lambda m: "" if ("showroad" in m.group(0).lower() or "emotion_video" in m.group(0).lower()) else m.group(0), sanitized_text, flags=_re.IGNORECASE)
            # Также удаляем нефенсенный одиночный JSON, если он состоит только из showroad/emotion_video
            sanitized_text = _re.sub(r"\{\s*\"showroad\"\s*:\s*true\s*\}", "", sanitized_text, flags=_re.IGNORECASE)
            sanitized_text = _re.sub(r"\{\s*\"emotion_video\"\s*:\s*\"[^\"]+\"\s*\}", "", sanitized_text, flags=_re.IGNORECASE)
            # НОВОЕ: параллельно проверяем упоминания моделей Эвотор и отправляем соответствующее изображение
            try:
                import asyncio as _asyncio
                _asyncio.create_task(_maybe_send_kkt_picture(original_text, chat_id))
            except Exception as _e:
                logger.warning(f"kktpictures: не удалось запустить отправку изображения: {_e}")
            if sanitized_text != original_text:
                logger.info("🧹 Удалены служебные JSON-блоки (showroad/emotion_video) без обрезки текста")
            logger.info("🔍 Ни IMAGE JSON, ни SPEAK JSON не найдены — возвращаем очищенный текст")
            return sanitized_text.strip()
        
        logger.info(f"🎨 Крутой парсер нашел JSON: {list(image_data.keys())}")
        
        # Ищем описание в разных полях
        description = image_data.get("description", "")
        if not description:
            description = image_data.get("Сцена", "")
        if not description:
            description = image_data.get("scene", "")
        if not description:
            description = image_data.get("Фокус", "")
        if not description:
            # Собираем описание из нескольких полей
            parts = []
            if image_data.get("Сцена"):
                parts.append(image_data["Сцена"])
            elif image_data.get("Фокус"):
                parts.append(image_data["Фокус"])
            if image_data.get("Стиль"):
                parts.append(f"стиль: {image_data['Стиль']}")
            if image_data.get("Цвета"):
                parts.append(f"цвета: {image_data['Цвета']}")
            description = ", ".join(parts)
        
        logger.info(f"🔍 Извлечено описание: '{description}'")
        
        if not description and image_data:
            logger.warning("🔍 Пустое описание изображения в JSON")
            # Не выходим — возможно есть SPEAK JSON
        
        cleaned_text = response_text
        import re
        # Если есть изображение — запускаем генерацию в фоне
        if description:
            logger.info(f"🎨 Запускаем генерацию изображения: {description[:50]}...")
            import asyncio
            asyncio.create_task(generate_image_in_background(chat_id, description))
            # Чистим IMAGE JSON из текста
            cleaned_text = re.sub(r'IMAGE!\s*(\{.*?\})', "", cleaned_text, flags=re.IGNORECASE | re.DOTALL)
            cleaned_text = re.sub(r'```json\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})', "", cleaned_text, flags=re.IGNORECASE | re.DOTALL)
            cleaned_text = re.sub(r'```\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})', "", cleaned_text, flags=re.IGNORECASE | re.DOTALL)

        # Если есть SPEAK — генерируем озвучку и отправляем голос
        if speak_params:
            logger.info(f"🎤 Найден SPEAK! JSON, запускаем TTS: {speak_params}")
            try:
                tts_dict = speak_params.get("tts") or speak_params
                
                # Ищем текст для озвучки ВНУТРИ JSON
                speak_text = speak_params.get("text", "")
                if not speak_text:
                    # Fallback: ищем текст вручную с помощью regex
                    text_match = re.search(r'"text":\s*"([^"]*)"', response_text)
                    if text_match:
                        speak_text = text_match.group(1)
                        logger.info(f"🎤 Fallback regex нашел текст: {speak_text[:100]}...")
                    else:
                        # Последний fallback: если нет поля text, берем весь ответ (старая логика)
                        cleaned_text = re.sub(r'SPEAK!\s*(\{[\s\S]*?\})', "", cleaned_text, flags=re.IGNORECASE)
                        speak_text = cleaned_text.strip()
                        logger.warning("🎤 Нет поля 'text' в SPEAK! JSON, используем весь ответ")
                else:
                    logger.info(f"🎤 Найден текст для озвучки в JSON: {speak_text[:100]}...")
                
                if speak_text:
                    tts = TextToSpeech()
                    audio_path = tts.text_to_speech_with_params(speak_text, tts_dict)
                    logger.info(f"🎤 TTS результат: {audio_path}")
                    if audio_path and os.path.exists(audio_path):
                        await send_voice_message(chat_id, audio_path)
                        # Убираем SPEAK! JSON из текстового ответа
                        cleaned_text = re.sub(r'SPEAK!\s*(\{[\s\S]*?\})', "", cleaned_text, flags=re.IGNORECASE)
                        # Дополнительно: на всякий случай срезаем всё от SPEAK! до конца, если что-то осталось
                        post_strip = cleaned_text
                        cleaned_text = re.sub(r'SPEAK![\s\S]*$', "", cleaned_text, flags=re.IGNORECASE)
                        if cleaned_text != post_strip:
                            logger.info(f"🧹 После отправки голоса удалён хвост от SPEAK!: '{post_strip[-100:]}' → '{cleaned_text[-100:]}'")
                        # Удаляем возможные хвосты параметров ElevenLabs, если они каким-то образом попали в текст
                        for key in ['model_id','output_format','stability','similarity_boost','style','use_speaker_boost']:
                            before = cleaned_text
                            cleaned_text = re.sub(rf',\s*"{key}"\s*:[\s\S]*$', "", cleaned_text, flags=re.IGNORECASE)
                            if cleaned_text != before:
                                logger.info(f"🧹 Обрезан хвост параметра '{key}' в тексте ответа")
                        cleaned_text = cleaned_text.strip()
                    else:
                        logger.error(f"🎤 TTS не создал файл: {audio_path}")
            except Exception as e:
                logger.error(f"Ошибка генерации/отправки озвучки: {e}")
        else:
            # Fallback: попробуем вытащить SPEAK! даже если парсер вернул пусто
            import re
            # Улучшенный паттерн для длинных JSON
            m = re.search(r'SPEAK!\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})', response_text, flags=re.IGNORECASE | re.DOTALL)
            if m:
                try:
                    import json
                    json_str = m.group(1)
                    # Обрабатываем длинные JSON как в robust_json_parser
                    fixed_json = json_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    fixed_json = re.sub(r'\\+', '\\', fixed_json)  # Убираем двойные слеши
                    
                    speak_obj = json.loads(fixed_json)
                    speak_text = speak_obj.get("text") or ""
                    tts_dict = speak_obj.get("tts") or {}
                    if speak_text:
                        logger.info(f"🎤 Fallback SPEAK найден, запускаем TTS")
                        tts = TextToSpeech()
                        audio_path = tts.text_to_speech_with_params(speak_text, tts_dict)
                        if audio_path and os.path.exists(audio_path):
                            await send_voice_message(chat_id, audio_path)
                            cleaned_text = re.sub(r'SPEAK!\s*(\{[\s\S]*?\})', "", cleaned_text, flags=re.IGNORECASE)
                        else:
                            logger.error("🎤 Fallback TTS не создал файл")
                except Exception as _e:
                    logger.warning(f"🎤 Fallback SPEAK парсинг не удался: {_e}")
            else:
                logger.info("🎤 SPEAK! JSON не найден, пропускаем TTS")

        cleaned_text = cleaned_text.strip()
        # НОВОЕ: проверяем упоминания моделей Эвотор и отправляем изображение (не изменяя текст)
        try:
            import asyncio as _asyncio
            _asyncio.create_task(_maybe_send_kkt_picture(response_text, chat_id))
        except Exception as _e:
            logger.warning(f"kktpictures: не удалось запустить отправку изображения: {_e}")
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Ошибка обработки изображения: {e}")
        return response_text


async def _maybe_send_kkt_picture(response_text: str, chat_id: str) -> None:
    """Проверяет упоминания моделей Эвотор в тексте и отправляет подходящее фото из kktpictures.

    Поддерживаемые соответствия:
      - Эвотор 10 -> kktpictures/10.jpeg
      - Эвотор 7.3 -> kktpictures/7.3.png
      - Эвотор 7.2 -> kktpictures/7.2.jpeg
      - Эвотор 6 -> kktpictures/6.jpeg
      - Эвотор 5i -> kktpictures/5i.png
      - Эвотор 5 -> kktpictures/5.jpeg
      - Эвотор Power (ФР) -> kktpictures/power.jpg
    Отправляется первая найденная релевантная картинка.
    """
    try:
        import os, re
        base_dir = "/root/IKAR-ASSISTANT/kktpictures"
        text = response_text.lower()
        patterns = [
            (r"эвотор\s*10\b|\bevotor\s*10\b|\bэватор\s*10\b", "10.jpeg"),
            (r"эвотор\s*7\s*[\.-]?\s*3\b|\bevotor\s*7\s*[\.-]?\s*3\b", "7.3.png"),
            (r"эвотор\s*7\s*[\.-]?\s*2\b|\bevotor\s*7\s*[\.-]?\s*2\b", "7.2.jpeg"),
            (r"эвотор\s*6\b|\bevotor\s*6\b", "6.jpeg"),
            (r"эвотор\s*5i\b|\bevotor\s*5i\b|эвотор\s*5i\b", "5i.png"),
            (r"эвотор\s*5\b|\bevotor\s*5\b", "5.jpeg"),
            (r"эвотор\s*power\b|power\s*фр\b|power\b|пауэр\b|пауер\b|фр\b", "power.jpg"),
            # ATOL / АТОЛ линейка
            (r"\b(атол|atol)\s*91\s*ф?\b|\b91ф\b", "91.png"),
            (r"\b(атол|atol)\s*30\s*ф?\b|\b30ф\b", "30.jpeg"),
            (r"\b(атол|atol)\s*20\s*ф?\b|\b20ф\b", "20.jpeg"),
            (r"\b(атол|atol)\s*sigma\s*10\b|\bсигма\s*10\b", "sigma10.jpeg"),
            (r"\b(атол|atol)\s*sigma\s*7\b|\bсигма\s*7\b", "sigma7.jpeg"),
            (r"\b(атол|atol)\s*sigma\s*8\b|\bсигма\s*8\b", "atol-sigma-8.png"),
        ]
        # Собираем ВСЕ совпадения с позицией появления
        hits = []  # (pos, filename)
        for pat, filename in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                hits.append((m.start(), filename))
        if not hits:
            return
        # Сортируем по позиции, берём до двух уникальных файлов
        hits.sort(key=lambda x: x[0])
        sent = set()
        to_send = []
        for _, fname in hits:
            if fname not in sent:
                to_send.append(fname)
                sent.add(fname)
            if len(to_send) >= 2:
                break
        for fname in to_send:
            path = os.path.join(base_dir, fname)
            if os.path.exists(path):
                logger.info(f"kktpictures: отправляем изображение модели: {fname}")
                await send_telegram_photo(chat_id, path)
            else:
                logger.warning(f"kktpictures: файл не найден: {path}")
    except Exception as e:
        logger.error(f"kktpictures: ошибка отправки изображения: {e}")
