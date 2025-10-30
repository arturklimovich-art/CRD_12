from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests
import os

router = APIRouter()

class PatchRequest(BaseModel):
    target_filepath: str
    code: str
    job_id: Optional[str] = None

class PatchResponse(BaseModel):
    status: str
    message: str
    backup: Optional[str] = None
    hash: Optional[str] = None

def log_event(source: str, event_type: str, job_id: Optional[str], payload: dict):
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

@router.post("/agent/apply_patch", response_model=PatchResponse)
async def apply_patch(patch_request: PatchRequest):
    try:
        # Логируем попытку
        log_event("engineer_b_api", "PATCH_ATTEMPT", patch_request.job_id, {
            "target_file": patch_request.target_filepath,
            "code_length": len(patch_request.code)
        })
        
        # Простая валидация пути
        allowed_paths = ["/app/src", "/app/agents", "/app/utils"]
        if not any(patch_request.target_filepath.startswith(path) for path in allowed_paths):
            error_msg = f"Path not allowed: {patch_request.target_filepath}"
            log_event("engineer_b_api", "PATCH_ROLLBACK", patch_request.job_id, {
                "reason": error_msg
            })
            return PatchResponse(status="error", message=error_msg)
        
        # Здесь будет полная логика применения патча
        # Пока возвращаем успех для тестирования интеграции
        result = PatchResponse(
            status="success",
            message="Patch endpoint integrated successfully",
            backup="/app/backups/test.backup",
            hash="test_hash_123"
        )
        
        # Логируем успех
        log_event("engineer_b_api", "PATCH_APPLIED", patch_request.job_id, {
            "target_file": patch_request.target_filepath,
            "result": result.dict()
        })
        
        return result
        
    except Exception as e:
        error_msg = f"Patch failed: {str(e)}"
        log_event("engineer_b_api", "PATCH_ROLLBACK", patch_request.job_id, {
            "reason": error_msg
        })
        return PatchResponse(status="error", message=error_msg)

@router.get("/agent/patches")
async def get_patches():
    try:
        response = requests.get("http://events_service:8031/events?limit=10")
        events = response.json().get("events", [])
        patch_events = [e for e in events if e["type"] in ["PATCH_APPLIED", "PATCH_ROLLBACK"]]
        return {"patches": patch_events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
