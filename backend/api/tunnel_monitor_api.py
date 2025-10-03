"""
API для мониторинга localtunnel сервисов
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import subprocess
import json
import os

logger = logging.getLogger(__name__)

tunnel_monitor_router = APIRouter()

# Глобальная переменная для менеджера туннелей
tunnel_manager = None

def get_tunnel_manager():
    """Получение менеджера туннелей"""
    global tunnel_manager
    if tunnel_manager is None:
        try:
            from backend.scripts.localtunnel_manager import LocaltunnelManager
            tunnel_manager = LocaltunnelManager()
        except Exception as e:
            logger.error(f"Ошибка инициализации менеджера туннелей: {e}")
            return None
    return tunnel_manager

@tunnel_monitor_router.get("/admin/tunnel_monitor/stats")
async def get_tunnel_stats():
    """Получение статистики туннелей"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        stats = manager.get_stats()
        return {"status": "ok", "stats": stats}
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики туннелей: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.get("/admin/tunnel_monitor/tunnels")
async def get_tunnels():
    """Получение списка всех туннелей"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        # Обновляем статусы всех туннелей
        manager.update_all_statuses()
        
        # Конвертируем в список для JSON
        tunnels = []
        for name, status in manager.tunnels.items():
            tunnels.append({
                "name": status.name,
                "subdomain": status.subdomain,
                "port": status.port,
                "url": status.url,
                "status": status.status,
                "uptime": status.uptime,
                "last_check": status.last_check,
                "response_time": status.response_time,
                "error_count": status.error_count,
                "last_error": status.last_error,
                "enabled": status.enabled
            })
        
        return {"status": "ok", "tunnels": tunnels}
        
    except Exception as e:
        logger.error(f"Ошибка получения списка туннелей: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.post("/admin/tunnel_monitor/start/{tunnel_name}")
async def start_tunnel(tunnel_name: str):
    """Запуск туннеля"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        # Находим конфигурацию туннеля
        tunnel_config = None
        for tunnel in manager.config['tunnels']:
            if tunnel['name'] == tunnel_name:
                tunnel_config = tunnel
                break
        
        if not tunnel_config:
            return JSONResponse(
                status_code=404,
                content={"error": f"Туннель {tunnel_name} не найден"}
            )
        
        success = manager.start_tunnel(tunnel_config)
        
        if success:
            return {"status": "ok", "message": f"Туннель {tunnel_name} запущен"}
        else:
            return JSONResponse(
                status_code=500,
                content={"error": f"Ошибка запуска туннеля {tunnel_name}"}
            )
        
    except Exception as e:
        logger.error(f"Ошибка запуска туннеля {tunnel_name}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.post("/admin/tunnel_monitor/stop/{tunnel_name}")
async def stop_tunnel(tunnel_name: str):
    """Остановка туннеля"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        success = manager.stop_tunnel(tunnel_name)
        
        if success:
            return {"status": "ok", "message": f"Туннель {tunnel_name} остановлен"}
        else:
            return JSONResponse(
                status_code=500,
                content={"error": f"Ошибка остановки туннеля {tunnel_name}"}
            )
        
    except Exception as e:
        logger.error(f"Ошибка остановки туннеля {tunnel_name}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.post("/admin/tunnel_monitor/restart/{tunnel_name}")
async def restart_tunnel(tunnel_name: str):
    """Перезапуск туннеля"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        success = manager.restart_tunnel(tunnel_name)
        
        if success:
            return {"status": "ok", "message": f"Туннель {tunnel_name} перезапущен"}
        else:
            return JSONResponse(
                status_code=500,
                content={"error": f"Ошибка перезапуска туннеля {tunnel_name}"}
            )
        
    except Exception as e:
        logger.error(f"Ошибка перезапуска туннеля {tunnel_name}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.post("/admin/tunnel_monitor/start_all")
async def start_all_tunnels():
    """Запуск всех включенных туннелей"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        manager.start_all_enabled()
        return {"status": "ok", "message": "Все включенные туннели запущены"}
        
    except Exception as e:
        logger.error(f"Ошибка запуска всех туннелей: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.post("/admin/tunnel_monitor/stop_all")
async def stop_all_tunnels():
    """Остановка всех туннелей"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        manager.stop_all()
        return {"status": "ok", "message": "Все туннели остановлены"}
        
    except Exception as e:
        logger.error(f"Ошибка остановки всех туннелей: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.post("/admin/tunnel_monitor/restart_all")
async def restart_all_tunnels():
    """Перезапуск всех туннелей"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        # Останавливаем все
        manager.stop_all()
        
        # Запускаем все включенные
        manager.start_all_enabled()
        
        return {"status": "ok", "message": "Все туннели перезапущены"}
        
    except Exception as e:
        logger.error(f"Ошибка перезапуска всех туннелей: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.get("/admin/tunnel_monitor/config")
async def get_config():
    """Получение конфигурации туннелей"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        return {"status": "ok", "config": manager.config}
        
    except Exception as e:
        logger.error(f"Ошибка получения конфигурации: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.post("/admin/tunnel_monitor/monitoring/start")
async def start_monitoring():
    """Запуск мониторинга"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        manager.start_monitoring()
        return {"status": "ok", "message": "Мониторинг запущен"}
        
    except Exception as e:
        logger.error(f"Ошибка запуска мониторинга: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@tunnel_monitor_router.post("/admin/tunnel_monitor/monitoring/stop")
async def stop_monitoring():
    """Остановка мониторинга"""
    try:
        manager = get_tunnel_manager()
        if not manager:
            return JSONResponse(
                status_code=500,
                content={"error": "Менеджер туннелей не инициализирован"}
            )
        
        manager.stop_monitoring()
        return {"status": "ok", "message": "Мониторинг остановлен"}
        
    except Exception as e:
        logger.error(f"Ошибка остановки мониторинга: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        ) 