import json
from pathlib import Path
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

triggers_path = Path(__file__).parent.parent / "admin_triggers.json"
autoposts_path = Path(__file__).parent.parent / "admin_autoposts.json"

router = APIRouter()

@router.get("/api/admin/triggers")
async def get_triggers():
    if triggers_path.exists():
        with open(triggers_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    else:
        data = []
    return data

@router.post("/api/admin/triggers")
async def set_triggers(data: list = Body(...)):
    try:
        if not isinstance(data, list):
            return JSONResponse(status_code=400, content={"detail": "Ожидается список триггеров"})
        with open(triggers_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"status": "ok", "saved": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@router.get("/api/admin/autoposts")
async def get_autoposts():
    if autoposts_path.exists():
        with open(autoposts_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    else:
        data = []
    return data

@router.post("/api/admin/autoposts")
async def set_autoposts(data: list = Body(...)):
    try:
        if not isinstance(data, list):
            return JSONResponse(status_code=400, content={"detail": "Ожидается список автопостов"})
        with open(autoposts_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"status": "ok", "saved": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
