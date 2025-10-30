from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import psycopg2
import psycopg2.extras
import json
import uvicorn
from datetime import datetime

app = FastAPI(
    title="Events Service",
    description="Полная система логирования событий Engineers_IT Core",
    version="2.1.0"
)

class EventLogRequest(BaseModel):
    source: str
    type: str  
    job_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class EventResponse(BaseModel):
    event_id: int
    status: str
    message: str

class SystemStatus(BaseModel):
    service: str
    status: str
    events_24h: int
    last_event: Optional[str] = None

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
    return {"status": "healthy", "service": "Events Service v2.1"}

@app.post("/events/log", response_model=EventResponse)
async def log_event(event: EventLogRequest):
    conn = None
    cursor = None
    try:
        print(f"Logging event: {event.source} - {event.type}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Валидация типа события
        valid_types = [
            'ANALYZE_OK', 'ANALYZE_ERROR', 'PATCH_ATTEMPT', 'PATCH_APPLIED', 
            'PATCH_ROLLBACK', 'RECOVERY_OK', 'RECOVERY_ATTEMPT', 'SMOKE_OK',
            'SMOKE_FAILED', 'SERVICE_STARTED', 'SERVICE_STOPPED', 
            'HEALTH_CHECK_OK', 'HEALTH_CHECK_FAILED', 'JOB_CREATED',
            'JOB_COMPLETED', 'JOB_FAILED', 'DATABASE_BACKUP_CREATED',
            'AUTO_RECOVERY_TRIGGERED'
        ]
        
        if event.type not in valid_types:
            return EventResponse(
                event_id=-1,
                status="error",
                message=f"Invalid event type: {event.type}. Valid types: {', '.join(valid_types)}"
            )
        
        payload_json = json.dumps(event.payload) if event.payload else None
        
        sql = """
            INSERT INTO core.events (source, type, job_id, payload) 
            VALUES (%s, %s, %s, %s) 
            RETURNING id
        """
        
        cursor.execute(sql, (event.source, event.type, event.job_id, payload_json))
        event_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"Event logged successfully: ID {event_id}")
        
        return EventResponse(
            event_id=event_id,
            status="success", 
            message=f"Event {event.type} logged with ID: {event_id}"
        )
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error logging event: {e}")
        return EventResponse(
            event_id=-1,
            status="error", 
            message=f"Database error: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.get("/events")
async def get_events(
    limit: int = 50,
    type_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
    hours: int = 24
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """
            SELECT id, ts, source, type, job_id, payload 
            FROM core.events 
            WHERE ts >= NOW() - INTERVAL '%s hours'
        """
        params = [hours]
        
        if type_filter:
            query += " AND type = %s"
            params.append(type_filter)
            
        if source_filter:
            query += " AND source = %s" 
            params.append(source_filter)
            
        query += " ORDER BY ts DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        events = cursor.fetchall()
        cursor.close()
        conn.close()
        
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
            ],
            "total": len(events),
            "filters": {
                "type": type_filter,
                "source": source_filter,
                "hours": hours
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/events/stats")
async def get_events_stats(hours: int = 24):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Статистика по типам событий
        cursor.execute("""
            SELECT 
                type,
                COUNT(*) as count,
                COUNT(DISTINCT source) as unique_sources
            FROM core.events 
            WHERE ts >= NOW() - INTERVAL '%s hours'
            GROUP BY type
            ORDER BY count DESC
        """, (hours,))
        
        type_stats = [
            {"type": row[0], "count": row[1], "unique_sources": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Статистика по источникам
        cursor.execute("""
            SELECT 
                source,
                COUNT(*) as count
            FROM core.events 
            WHERE ts >= NOW() - INTERVAL '%s hours'
            GROUP BY source
            ORDER BY count DESC
        """, (hours,))
        
        source_stats = [
            {"source": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]
        
        cursor.close()
        conn.close()
        
        return {
            "period_hours": hours,
            "type_statistics": type_stats,
            "source_statistics": source_stats,
            "total_events": ( | Measure-Object -Property count -Sum).Sum
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/status")
async def get_system_status():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Статус системы на основе событий
        cursor.execute("""
            SELECT 
                'events_service' as service,
                'healthy' as status,
                COUNT(*) as events_24h,
                MAX(ts) as last_event
            FROM core.events 
            WHERE ts >= NOW() - INTERVAL '24 hours'
        """)
        
        status = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return SystemStatus(
            service=status[0],
            status=status[1],
            events_24h=status[2],
            last_event=status[3].isoformat() if status[3] else None
        )
    except Exception as e:
        return SystemStatus(
            service="events_service",
            status="error",
            events_24h=0,
            last_event=None
        )

if __name__ == "__main__":
    print("Starting Events Service v2.1 with full event integration...")
    uvicorn.run(app, host="0.0.0.0", port=8031, log_level="info")
