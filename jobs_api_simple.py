from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import psycopg2
import json
import uuid

router = APIRouter()

class JobCreateRequest(BaseModel):
    source: str
    task_type: str
    meta: Optional[Dict[str, Any]] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    source: str
    task_type: str
    created_at: str

def get_db_connection():
    return psycopg2.connect(
        host="pgvector",
        database="crd12",
        user="crd_user",
        password="crd12", 
        port="5432"
    )

@router.post("/jobs", response_model=JobResponse)
async def create_job(job_request: JobCreateRequest):
    conn = None
    try:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Создаем задание в БД
        cursor.execute(
            "INSERT INTO core.jobs (job_id, status, source, task_type, meta) VALUES (%s, %s, %s, %s, %s) RETURNING job_id, status, source, task_type, created_at",
            (job_id, 'pending', job_request.source, job_request.task_type, json.dumps(job_request.meta) if job_request.meta else None)
        )
        
        job_data = cursor.fetchone()
        conn.commit()
        
        # Логируем событие
        try:
            import requests
            event_data = {
                "source": "engineer_b_api",
                "type": "JOB_CREATED", 
                "job_id": job_id,
                "payload": {
                    "source": job_request.source,
                    "task_type": job_request.task_type
                }
            }
            requests.post("http://events_service:8031/events/log", json=event_data, timeout=3)
        except:
            pass  # Игнорируем ошибки логирования
        
        return JobResponse(
            job_id=job_data[0],
            status=job_data[1],
            source=job_data[2],
            task_type=job_data[3],
            created_at=job_data[4].isoformat()
        )
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")
    finally:
        if conn:
            conn.close()

@router.get("/jobs/simple-test")
async def simple_test():
    return {"message": "Jobs API is working!", "status": "success"}

@router.get("/jobs/stats")
async def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM core.jobs")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM core.jobs WHERE status = 'success'")
        success = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_jobs": total,
            "successful_jobs": success,
            "success_rate": round((success / total * 100), 2) if total > 0 else 0
        }
    except Exception as e:
        return {"error": str(e)}
