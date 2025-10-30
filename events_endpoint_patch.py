# Патч для добавления эндпоинта событий в Engineer_B_API
# Файл: /app/events_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import asyncpg
import os
from typing import Optional, Dict, Any

router = APIRouter()

class EventLogRequest(BaseModel):
    source: str
    type: str
    job_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class EventLogResponse(BaseModel):
    event_id: int
    status: str
    message: str

@router.post("/events/log", response_model=EventLogResponse)
async def log_event(event: EventLogRequest):
    \"\"\"
    Логирование события в БД (таблица core.events)
    \"\"\"
    try:
        # Подключение к БД
        database_url = os.getenv("DATABASE_URL")
        conn = await asyncpg.connect(database_url)
        
        # Вставляем событие в БД
        query = \"\"\"
            INSERT INTO core.events (source, type, job_id, payload)
            VALUES (, , , )
            RETURNING id
        \"\"\"
        
        event_id = await conn.fetchval(
            query, 
            event.source,
            event.type, 
            event.job_id,
            event.payload
        )
        
        await conn.close()
        
        return EventLogResponse(
            event_id=event_id,
            status="success",
            message=f"Event logged with ID: {event_id}"
        )
        
    except Exception as e:
        # Логируем ошибку, но не падаем
        print(f"Error logging event: {e}")
        return EventLogResponse(
            event_id=-1,
            status="error",
            message=f"Failed to log event: {str(e)}"
        )

# Эндпоинт для проверки событий (для отладки)
@router.get("/events")
async def get_recent_events(limit: int = 10):
    \"\"\"Получить последние события\"\"\"
    try:
        database_url = os.getenv("DATABASE_URL")
        conn = await asyncpg.connect(database_url)
        
        query = \"\"\"
            SELECT id, ts, source, type, job_id, payload
            FROM core.events 
            ORDER BY ts DESC 
            LIMIT 
        \"\"\"
        
        events = await conn.fetch(query, limit)
        await conn.close()
        
        return {
            "events": [
                {
                    "id": e["id"],
                    "ts": e["ts"].isoformat(),
                    "source": e["source"],
                    "type": e["type"],
                    "job_id": e["job_id"],
                    "payload": e["payload"]
                }
                for e in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Инструкция по интеграции:
# 1. Скопировать этот код в /app/events_router.py в контейнере
# 2. В /app/main.py добавить: from events_router import router as events_router
# 3. В /app/main.py добавить: app.include_router(events_router, tags=["events"])
# 4. Перезапустить uvicorn процесс через supervisor
