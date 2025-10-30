# apply_patch_router.py
# Router для эндпоинтов управления патчами
# Интеграция в Engineer_B_API

import os
import hashlib
import shutil
import py_compile
import importlib.util
import requests
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

class PatchRequest(BaseModel):
    target_filepath: str
    code: str
    job_id: Optional[str] = None

class PatchResponse(BaseModel):
    status: str  # applied | rollback | error
    backup: Optional[str] = None
    hash: Optional[str] = None  
    post_health: Optional[str] = None
    message: Optional[str] = None

def log_event(source: str, event_type: str, job_id: Optional[str], payload: Dict[str, Any]):
    \"\"\"Логирование события через микросервис\"\"\"
    try:
        event_data = {
            "source": source,
            "type": event_type,
            "job_id": job_id,
            "payload": payload
        }
        response = requests.post(
            "http://events_service:8031/events/log",
            json=event_data,
            timeout=5
        )
        return response.json()
    except Exception as e:
        print(f"Failed to log event: {e}")
        return None

def validate_filepath(filepath: str) -> bool:
    \"\"\"Валидация пути файла\"\"\"
    allowed_paths = ["/app/src", "/app/agents", "/app/utils"]
    return any(filepath.startswith(path) for path in allowed_paths)

def safe_import_module(filepath: str) -> bool:
    \"\"\"Безопасный импорт модуля для smoke-теста\"\"\"
    try:
        module_name = os.path.splitext(os.path.basename(filepath))[0]
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True
    except Exception as e:
        print(f"Smoke test failed: {e}")
        return False

@router.post("/agent/apply_patch", response_model=PatchResponse)
async def apply_patch(patch_request: PatchRequest):
    \"\"\"
    Безопасное применение патча с атомарными операциями
    \"\"\"
    target_file = patch_request.target_filepath
    new_code = patch_request.code
    job_id = patch_request.job_id
    
    # Логирование начала операции
    log_event("engineer_b_api", "PATCH_ATTEMPT", job_id, {
        "target_file": target_file,
        "code_length": len(new_code),
        "code_hash": hashlib.sha256(new_code.encode()).hexdigest()
    })
    
    # 1. Валидация пути
    if not validate_filepath(target_file):
        error_msg = f"Path not allowed: {target_file}"
        log_event("engineer_b_api", "PATCH_ROLLBACK", job_id, {
            "reason": error_msg, "target_file": target_file
        })
        return PatchResponse(status="error", message=error_msg)
    
    # 2. Подготовка директорий
    backup_dir = "/app/backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_file = None
    tmp_file = target_file + ".tmp"
    
    try:
        # 3. Создание бэкапа (если файл существует)
        if os.path.exists(target_file):
            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            backup_file = f"{backup_dir}/{os.path.basename(target_file)}.{timestamp}.bak"
            shutil.copy2(target_file, backup_file)
        
        # 4. Запись нового кода во временный файл
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(new_code)
        
        # 5. Проверка синтаксиса
        py_compile.compile(tmp_file, doraise=True)
        
        # 6. Атомарный swap
        os.replace(tmp_file, target_file)
        
        # 7. Smoke-тест
        if not safe_import_module(target_file):
            raise Exception("Smoke test failed - module import error")
        
        # 8. Graceful restart (сигнал supervisor)
        # В реальной реализации здесь будет вызов supervisorctl
        print("Would restart supervisor here...")
        
        # 9. Логирование успеха
        log_event("engineer_b_api", "PATCH_APPLIED", job_id, {
            "target_file": target_file,
            "backup_file": backup_file,
            "code_hash": hashlib.sha256(new_code.encode()).hexdigest(),
            "file_size": len(new_code)
        })
        
        return PatchResponse(
            status="applied",
            backup=backup_file,
            hash=hashlib.sha256(new_code.encode()).hexdigest(),
            post_health="ok",
            message="Patch applied successfully"
        )
        
    except Exception as e:
        # 10. Откат при ошибке
        error_msg = f"Patch failed: {str(e)}"
        print(error_msg)
        
        # Восстановление из бэкапа
        if backup_file and os.path.exists(backup_file):
            try:
                shutil.copy2(backup_file, target_file)
                print(f"Restored from backup: {backup_file}")
            except Exception as restore_error:
                print(f"Backup restore failed: {restore_error}")
        
        # Удаление временного файла
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        
        # Логирование ошибки
        log_event("engineer_b_api", "PATCH_ROLLBACK", job_id, {
            "reason": str(e),
            "target_file": target_file,
            "backup_file": backup_file
        })
        
        return PatchResponse(
            status="rollback",
            backup=backup_file,
            message=error_msg
        )

# Эндпоинт для проверки примененных патчей
@router.get("/agent/patches")
async def get_recent_patches(limit: int = 10):
    \"\"\"Получить информацию о последних патчах\"\"\"
    try:
        response = requests.get(f"http://events_service:8031/events?limit={limit}")
        events = response.json().get("events", [])
        
        patch_events = [
            event for event in events 
            if event["type"] in ["PATCH_APPLIED", "PATCH_ROLLBACK"]
        ]
        
        return {"patches": patch_events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patches: {str(e)}")

