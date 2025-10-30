from fastapi import APIRouter
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

@router.get("/jobs/test")
async def jobs_test():
    return {"message": "Jobs API is working!", "status": "success"}

@router.post("/jobs/create")
async def create_job(job_request: JobCreateRequest):
    try:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        conn = psycopg2.connect(
            host="pgvector",
            database="crd12",
            user="crd_user",
            password="crd12",
            port="5432"
        )
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO core.jobs (job_id, status, source, task_type, meta) VALUES (%s, %s, %s, %s, %s)",
            (job_id, 'pending', job_request.source, job_request.task_type, json.dumps(job_request.meta) if job_request.meta else None)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Логируем событие
        try:
            import requests
            requests.post("http://events_service:8031/events/log", json={
                "source": "engineer_b_api",
                "type": "JOB_CREATED",
                "job_id": job_id,
                "payload": {"source": job_request.source, "task_type": job_request.task_type}
            }, timeout=3)
        except:
            pass
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            source=job_request.source,
            task_type=job_request.task_type
        )
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@router.get("/jobs/list")
async def list_jobs():
    try:
        conn = psycopg2.connect(
            host="pgvector",
            database="crd12",
            user="crd_user",
            password="crd12", 
            port="5432"
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT job_id, status, source, task_type, created_at FROM core.jobs ORDER BY created_at DESC LIMIT 5")
        jobs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "jobs": [
                {
                    "job_id": j[0],
                    "status": j[1],
                    "source": j[2],
                    "task_type": j[3],
                    "created_at": j[4].isoformat()
                }
                for j in jobs
            ]
        }
    except Exception as e:
        return {"error": str(e)}
