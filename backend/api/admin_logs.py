import json
from pathlib import Path
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from datetime import datetime

router = APIRouter()
logs_path = Path(__file__).parent.parent / "admin_logs.json"

@router.get("/api/admin/logs")
async def get_logs(
    group: str = Query(None),
    user: str = Query(None),
    log_type: str = Query(None),
    after: str = Query(None),
    before: str = Query(None)
):
    if logs_path.exists():
        with open(logs_path, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except Exception:
                logs = []
    else:
        logs = []
    # Фильтрация
    def match(log):
        if group and log.get("group") != group:
            return False
        if user and log.get("user") != user:
            return False
        if log_type and log.get("type") != log_type:
            return False
        if after:
            try:
                after_dt = datetime.fromisoformat(after)
                if datetime.fromisoformat(log.get("time", "1970-01-01T00:00:00")) < after_dt:
                    return False
            except Exception:
                pass
        if before:
            try:
                before_dt = datetime.fromisoformat(before)
                if datetime.fromisoformat(log.get("time", "1970-01-01T00:00:00")) > before_dt:
                    return False
            except Exception:
                pass
        return True
    filtered = [log for log in logs if match(log)]
    return filtered[-200:]  # Ограничение на 200 последних записей
