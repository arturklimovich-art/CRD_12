# src/engineer_b_api/routes/patches.py
import uuid
import hashlib
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Optional, List
import psycopg2

router = APIRouter(prefix="/api/patches", tags=["patches"])

# Функции для работы с БД и событиями (временная реализация)
def get_db_connection():
    """Подключение к БД"""
    try:
        return psycopg2.connect(
            host="localhost",
            port=5433,
            database="crd12",
            user="crd_user",
            password="crd12"
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def send_system_event(event_type: str, payload: dict):
    """Отправка системных событий"""
    print(f"SYSTEM EVENT: {event_type} - {payload}")
    # TODO: Интегрировать с основной системой событий

# Pydantic модели
class PatchCreateRequest(BaseModel):
    author: str
    task_id: Optional[str] = None
    filename: str

class PatchResponse(BaseModel):
    id: str
    author: str
    filename: str
    sha256: str
    status: str
    created_at: datetime
    meta: dict

class PatchEventResponse(BaseModel):
    id: int
    ts: datetime
    event_type: str
    payload: dict

class PatchDetailResponse(PatchResponse):
    events: List[PatchEventResponse]
    applied_at: Optional[datetime] = None
    rollback_at: Optional[datetime] = None

@router.post("", response_model=PatchResponse)
async def create_patch(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    author: str = Form(...),
    task_id: Optional[str] = Form(None)
):
    """Загрузить новый патч в систему"""
    try:
        # Читаем и проверяем файл
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="File too large")
        
        # Вычисляем хеш
        sha256 = hashlib.sha256(content).hexdigest()
        
        # Сохраняем в БД
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                patch_id = str(uuid.uuid4())
                meta = {
                    "size": len(content),
                    "mime_type": file.content_type,
                    "original_filename": file.filename
                }
                
                cur.execute("""
                    INSERT INTO eng_it.patches 
                    (id, author, filename, content, sha256, status, task_id, meta)
                    VALUES (%s, %s, %s, %s, %s, 'submitted', %s, %s)
                    RETURNING id, author, filename, sha256, status, created_at, meta
                """, (patch_id, author, file.filename, content, sha256, task_id, meta))
                
                result = cur.fetchone()
                conn.commit()
                
                # Записываем событие
                cur.execute("""
                    INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
                    VALUES (%s, 'patch.submitted', %s)
                """, (patch_id, {"author": author, "filename": file.filename}))
                conn.commit()
        
        # Системное событие
        background_tasks.add_task(
            send_system_event,
            "plan.patch.submitted",
            {"patch_id": patch_id, "author": author, "filename": file.filename}
        )
        
        return {
            "id": result[0],
            "author": result[1],
            "filename": result[2],
            "sha256": result[3],
            "status": result[4],
            "created_at": result[5],
            "meta": result[6]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patch creation failed: {str(e)}")

@router.get("/{patch_id}", response_model=PatchDetailResponse)
async def get_patch(patch_id: str):
    """Получить информацию о патче"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Основная информация о патче
                cur.execute("""
                    SELECT id, author, filename, sha256, status, created_at, 
                           applied_at, rollback_at, meta
                    FROM eng_it.patches WHERE id = %s
                """, (patch_id,))
                patch = cur.fetchone()
                
                if not patch:
                    raise HTTPException(status_code=404, detail="Patch not found")
                
                # События патча
                cur.execute("""
                    SELECT id, ts, event_type, payload
                    FROM eng_it.patch_events 
                    WHERE patch_id = %s 
                    ORDER BY ts ASC
                """, (patch_id,))
                events = cur.fetchall()
                
                return {
                    "id": patch[0],
                    "author": patch[1],
                    "filename": patch[2],
                    "sha256": patch[3],
                    "status": patch[4],
                    "created_at": patch[5],
                    "applied_at": patch[6],
                    "rollback_at": patch[7],
                    "meta": patch[8],
                    "events": [
                        {
                            "id": event[0],
                            "ts": event[1],
                            "event_type": event[2],
                            "payload": event[3]
                        } for event in events
                    ]
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patch: {str(e)}")

@router.get("", response_model=List[PatchResponse])
async def list_patches(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000)
):
    """Получить список патчей"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT id, author, filename, sha256, status, created_at, meta
                    FROM eng_it.patches
                """
                params = []
                
                if status:
                    query += " WHERE status = %s"
                    params.append(status)
                
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                patches = cur.fetchall()
                
                return [
                    {
                        "id": patch[0],
                        "author": patch[1],
                        "filename": patch[2],
                        "sha256": patch[3],
                        "status": patch[4],
                        "created_at": patch[5],
                        "meta": patch[6]
                    } for patch in patches
                ]
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list patches: {str(e)}")
