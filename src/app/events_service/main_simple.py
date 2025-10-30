from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import psycopg2
import json
import uvicorn

app = FastAPI(title="Events Service", version="2.0")

class EventLogRequest(BaseModel):
    source: str
    type: str  
    job_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class EventResponse(BaseModel):
    event_id: int
    status: str
    message: str

def get_db_connection():
    return psycopg2.connect(
        host="pgvector",
        database="crd12", 
        user="crd_user",
        password="crd12",
        port="5432"
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Events Service"}

@app.post("/events/log", response_model=EventResponse)
async def log_event(event: EventLogRequest):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        payload_json = json.dumps(event.payload) if event.payload else None
        
        cursor.execute(
            "INSERT INTO core.events (source, type, job_id, payload) VALUES (%s, %s, %s, %s) RETURNING id",
            (event.source, event.type, event.job_id, payload_json)
        )
        
        event_id = cursor.fetchone()[0]
        conn.commit()
        
        return EventResponse(
            event_id=event_id,
            status="success", 
            message=f"Event logged with ID: {event_id}"
        )
        
    except Exception as e:
        if conn:
            conn.rollback()
        return EventResponse(
            event_id=-1,
            status="error", 
            message=f"Error: {str(e)}"
        )
    finally:
        if conn:
            conn.close()

@app.get("/events")
async def get_events(limit: int = 10):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, ts, source, type, job_id, payload FROM core.events ORDER BY ts DESC LIMIT %s",
            (limit,)
        )
        
        events = cursor.fetchall()
        conn.close()
        
        return {
            "events": [
                {
                    "id": e[0],
                    "ts": e[1].isoformat(),
                    "source": e[2],
                    "type": e[3],
                    "job_id": e[4],
                    "payload": e[5]
                }
                for e in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events/stats")
async def get_events_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM core.events WHERE ts >= NOW() - INTERVAL '24 hours'")
        count_24h = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM core.events")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT type) FROM core.events")
        unique_types = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "events_24h": count_24h,
            "total_events": total_count,
            "unique_event_types": unique_types
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("Starting Simple Events Service...")
    uvicorn.run(app, host="0.0.0.0", port=8031, log_level="info")
