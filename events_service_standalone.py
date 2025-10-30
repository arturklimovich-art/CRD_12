# Безопасный подход - создаем отдельный сервис для событий
# Файл: /app/events_service.py - можно запустить параллельно

from fastapi import FastAPI
import asyncpg
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel

app = FastAPI(title="Events Service")

class EventLogRequest(BaseModel):
    source: str
    type: str  
    job_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

@app.post("/log")
async def log_event(event: EventLogRequest):
    \"\"\"Логирование события через отдельный сервис\"\"\"
    try:
        database_url = os.getenv("DATABASE_URL")
        conn = await asyncpg.connect(database_url)
        
        event_id = await conn.fetchval(
            \"\"\"INSERT INTO core.events (source, type, job_id, payload)
                VALUES (, , , ) RETURNING id\"\"\",
            event.source, event.type, event.job_id, event.payload
        )
        
        await conn.close()
        return {"event_id": event_id, "status": "success"}
        
    except Exception as e:
        return {"event_id": -1, "status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8031)
