"""
Админские API функции для управления группами и каналами.
"""
import logging
import os
import sqlite3
from typing import Dict, Any, Optional
from fastapi import APIRouter, Body, Depends, Header, Request, HTTPException
from fastapi.responses import JSONResponse
import json
from pathlib import Path

from backend.memory.sqlite import SQLiteStorage

logger = logging.getLogger("chatumba.admin_api")

# Глобальные компоненты
sqlite_storage = SQLiteStorage()

# Простая защита админ-эндпоинтов токеном.
# Если переменная окружения ADMIN_API_TOKEN не задана — доступ открыт (dev-режим).
def require_admin(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_token: Optional[str] = Header(None)
):
    token = os.environ.get("ADMIN_API_TOKEN", "").strip()
    if not token:
        return
    provided: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()
    if not provided and x_admin_token:
        provided = x_admin_token.strip()
    if not provided:
        provided = request.query_params.get("token")
    if provided != token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return

# Создаем роутер
admin_router = APIRouter(dependencies=[Depends(require_admin)])

PROMPTS_PATH = Path(__file__).parent.parent / "admin_prompts.json"

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
    # Импортируем функцию здесь, чтобы избежать циклических импортов
    from api.telegram_core import analyze_group_history
    
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
    # Импортируем здесь, чтобы избежать циклических импортов
    from config import TELEGRAM_CONFIG
    from api.telegram_core import check_channel_permissions
    
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
    from config import TELEGRAM_CONFIG
    
    try:
        enabled = data.get("enabled", False)
        TELEGRAM_CONFIG["enable_channel_posting"] = enabled
        status = "включен" if enabled else "отключен"
        logger.info(f"[ADMIN] Постинг в канал {status}")
        return {"status": "ok", "enabled": enabled, "message": f"Постинг в канал {status}"}
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при переключении канала: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.get("/admin/prompts")
async def get_admin_prompts():
    """Получить все промпты по функциям (например, group_chat, photo_confirmation и т.д.)."""
    if PROMPTS_PATH.exists():
        with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    else:
        data = {}
    # Гарантируем наличие хотя бы одной функции для UI
    if not data:
        data = {
            "group_chat": {"system_prompt": "", "user_prompt": ""},
            "photo_confirmation": {"system_prompt": "", "user_prompt": ""}
        }
    return data

@admin_router.post("/admin/prompts")
async def save_admin_prompts(prompts: dict = Body(...)):
    """Обновить все промпты по функциям (ожидается словарь {function: {system_prompt, user_prompt}})."""
    try:
        # Валидация: только словарь {function: {system_prompt, user_prompt}}
        if not isinstance(prompts, dict):
            return JSONResponse(status_code=400, content={"detail": "Ожидается словарь функций"})
        for func, prompts in prompts.items():
            if not isinstance(prompts, dict):
                return JSONResponse(status_code=400, content={"detail": f"Промпты для {func} должны быть словарём"})
            if "system_prompt" not in prompts or "user_prompt" not in prompts:
                return JSONResponse(status_code=400, content={"detail": f"Для {func} нужны system_prompt и user_prompt"})
        with open(PROMPTS_PATH, "w", encoding="utf-8") as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        return {"status": "ok", "saved": prompts}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.get("/admin/memory_optimizer/status")
async def get_memory_optimizer_status():
    """Получает статус оптимизатора памяти."""
    try:
        from memory.memory_optimizer import get_memory_optimizer
        
        optimizer = get_memory_optimizer()
        
        if optimizer:
            stats = await optimizer.get_optimization_stats()
            return {"status": "ok", "optimizer": stats}
        else:
            return {"status": "ok", "optimizer": None, "message": "Оптимизатор не инициализирован"}
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка получения статуса оптимизатора: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.post("/admin/memory_optimizer/start")
async def start_memory_optimizer():
    """Запускает оптимизатор памяти."""
    try:
        from memory.memory_optimizer import start_background_optimization, get_memory_optimizer
        from llm import OpenRouterClient
        from config import Config
        
        # Проверяем, не запущен ли уже
        optimizer = get_memory_optimizer()
        if optimizer and optimizer.is_running:
            return {"status": "already_running", "message": "Оптимизатор уже запущен"}
        
        # Запускаем оптимизацию
        from utils.component_manager import get_component_manager
        component_manager = get_component_manager()
        llm_client = component_manager.get_llm_client()
        await start_background_optimization(sqlite_storage.db_path, llm_client)
        
        logger.info("[ADMIN] Оптимизатор памяти запущен")
        return {"status": "ok", "message": "Оптимизатор памяти запущен"}
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка запуска оптимизатора: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.post("/admin/memory_optimizer/stop")
async def stop_memory_optimizer():
    """Останавливает оптимизатор памяти."""
    try:
        from memory.memory_optimizer import stop_background_optimization, get_memory_optimizer
        
        optimizer = get_memory_optimizer()
        if not optimizer or not optimizer.is_running:
            return {"status": "not_running", "message": "Оптимизатор не запущен"}
        
        stop_background_optimization()
        
        logger.info("[ADMIN] Оптимизатор памяти остановлен")
        return {"status": "ok", "message": "Оптимизатор памяти остановлен"}
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка остановки оптимизатора: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.post("/admin/memory_optimizer/test")
async def test_memory_optimizer():
    """Тестирует оптимизатор памяти (один цикл)."""
    try:
        from memory.memory_optimizer import test_optimization
        from utils.component_manager import get_component_manager
        
        component_manager = get_component_manager()
        llm_client = component_manager.get_llm_client()
        await test_optimization(sqlite_storage.db_path, llm_client)
        
        logger.info("[ADMIN] Тестовая оптимизация выполнена")
        return {"status": "ok", "message": "Тестовая оптимизация выполнена"}
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка тестовой оптимизации: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@admin_router.post("/admin/memory_optimizer/config")
async def update_memory_optimizer_config(data: dict = Body(...)):
    """Обновляет конфигурацию оптимизатора памяти."""
    try:
        from memory.memory_optimizer import get_memory_optimizer
        
        optimizer = get_memory_optimizer()
        if not optimizer:
            return JSONResponse(status_code=400, content={"detail": "Оптимизатор не инициализирован"})
        
        # Обновляем настройки
        if "optimization_interval" in data:
            interval = int(data["optimization_interval"])
            if 60 <= interval <= 3600:  # От 1 минуты до 1 часа
                optimizer.optimization_interval = interval
                logger.info(f"[ADMIN] Интервал оптимизации изменен на {interval} секунд")
        
        if "max_chunk_tokens" in data:
            tokens = int(data["max_chunk_tokens"])
            if 10000 <= tokens <= 100000:  # От 10K до 100K токенов
                optimizer.max_chunk_tokens = tokens
                logger.info(f"[ADMIN] Максимальный размер чанка изменен на {tokens} токенов")
        
        if "night_start" in data and "night_end" in data:
            from datetime import time
            try:
                start_hour, start_min = map(int, data["night_start"].split(":"))
                end_hour, end_min = map(int, data["night_end"].split(":"))
                optimizer.night_start = time(start_hour, start_min)
                optimizer.night_end = time(end_hour, end_min)
                logger.info(f"[ADMIN] Ночное время изменено на {optimizer.night_start} - {optimizer.night_end}")
            except (ValueError, AttributeError):
                return JSONResponse(status_code=400, content={"detail": "Неверный формат времени (используйте HH:MM)"})
        
        return {"status": "ok", "message": "Конфигурация обновлена"}
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка обновления конфигурации: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

