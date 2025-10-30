from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import psycopg2
import psycopg2.extras
import json
import uuid
from datetime import datetime

router = APIRouter()

class JobCreateRequest(BaseModel):
    source: str
    task_type: str
    meta: Optional[Dict[str, Any]] = None

class JobUpdateRequest(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    status: str
    source: str
    task_type: str
    meta: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None

def get_db_connection():
    return psycopg2.connect(
        host="pgvector",
        database="crd12",
        user="crd_user", 
        password="crd12",
        port="5432"
    )

def log_event(source: str, event_type: str, job_id: Optional[str], payload: Dict[str, Any]):
    try:
        import requests
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

@router.post("/jobs", response_model=JobResponse)
async def create_job(job_request: JobCreateRequest):
    conn = None
    try:
        job_id = f"job_{uuid.uuid4().hex[:16]}"
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cursor.execute(
            "SELECT * FROM core.create_job(%s, %s, %s, %s)",
            (job_id, job_request.source, job_request.task_type, json.dumps(job_request.meta) if job_request.meta else None)
        )
        
        job_data = cursor.fetchone()
        conn.commit()
        
        # Логируем создание задания
        log_event("engineer_b_api", "JOB_CREATED", job_id, {
            "source": job_request.source,
            "task_type": job_request.task_type,
            "meta": job_request.meta
        })
        
        return JobResponse(
            job_id=job_data['job_id'],
            created_at=job_data['created_at'].isoformat(),
            status=job_data['status'],
            source=job_data['source'],
            task_type=job_data['task_type'],
            meta=job_data['meta']
        )
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")
    finally:
        if conn:
            conn.close()

@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, update_request: JobUpdateRequest):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cursor.execute(
            "SELECT * FROM core.update_job_status(%s, %s, %s, %s)",
            (job_id, update_request.status, 
             json.dumps(update_request.result) if update_request.result else None,
             update_request.error_message)
        )
        
        job_data = cursor.fetchone()
        if not job_data:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            
        conn.commit()
        
        # Логируем изменение статуса
        event_type = f"JOB_{update_request.status.upper()}"
        log_event("engineer_b_api", event_type, job_id, {
            "previous_status": "pending",  # В реальности нужно хранить предыдущий статус
            "new_status": update_request.status,
            "result": update_request.result,
            "error": update_request.error_message
        })
        
        response = JobResponse(
            job_id=job_data['job_id'],
            created_at=job_data['created_at'].isoformat(),
            started_at=job_data['started_at'].isoformat() if job_data['started_at'] else None,
            finished_at=job_data['finished_at'].isoformat() if job_data['finished_at'] else None,
            status=job_data['status'],
            source=job_data['source'],
            task_type=job_data['task_type'],
            meta=job_data['meta'],
            result=job_data['result'],
            error_message=job_data['error_message']
        )
        
        # Добавляем длительность если задание завершено
        if job_data['finished_at'] and job_data['started_at']:
            duration = (job_data['finished_at'] - job_data['started_at']).total_seconds()
            response.duration_seconds = duration
            
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update job: {str(e)}")
    finally:
        if conn:
            conn.close()

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cursor.execute("""
            SELECT 
                job_id, created_at, started_at, finished_at, status,
                source, task_type, meta, result, error_message,
                CASE 
                    WHEN finished_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (finished_at - started_at))
                    ELSE NULL
                END as duration_seconds
            FROM core.jobs 
            WHERE job_id = %s
        """, (job_id,))
        
        job_data = cursor.fetchone()
        if not job_data:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            
        return JobResponse(**dict(job_data))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")
    finally:
        if conn:
            conn.close()

@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(limit: int = 20, status: Optional[str] = None):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """
            SELECT 
                job_id, created_at, started_at, finished_at, status,
                source, task_type, meta, result, error_message,
                CASE 
                    WHEN finished_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (finished_at - started_at))
                    ELSE NULL
                END as duration_seconds
            FROM core.jobs
        """
        params = []
        
        if status:
            query += " WHERE status = %s"
            params.append(status)
            
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        jobs = cursor.fetchall()
        
        return [JobResponse(**dict(job)) for job in jobs]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")
    finally:
        if conn:
            conn.close()

@router.get("/jobs/overview/stats")
async def get_jobs_stats(hours: int = 24):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Статистика по статусам
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM core.jobs 
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            GROUP BY status
        """, (hours,))
        
        status_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Статистика по источникам
        cursor.execute("""
            SELECT 
                source,
                COUNT(*) as count
            FROM core.jobs 
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            GROUP BY source
            ORDER BY count DESC
        """, (hours,))
        
        source_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Среднее время выполнения
        cursor.execute("""
            SELECT 
                AVG(EXTRACT(EPOCH FROM (finished_at - started_at))) as avg_duration
            FROM core.jobs 
            WHERE status = 'success' 
            AND finished_at IS NOT NULL 
            AND started_at IS NOT NULL
            AND created_at >= NOW() - INTERVAL '%s hours'
        """, (hours,))
        
        avg_duration = cursor.fetchone()[0] or 0
        
        return {
            "period_hours": hours,
            "status_statistics": status_stats,
            "source_statistics": source_stats,
            "average_duration_seconds": round(avg_duration, 2),
            "total_jobs": sum(status_stats.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get jobs stats: {str(e)}")
    finally:
        if conn:
            conn.close()
