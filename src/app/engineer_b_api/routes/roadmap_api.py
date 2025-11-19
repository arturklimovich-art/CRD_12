# src/app/engineer_b_api/routes/roadmap_api.py
"""
Roadmap JSON API endpoints for Bot v2 integration
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

router = APIRouter(prefix="/api", tags=["roadmap"])

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "crd12_pgvector"),
        port=int(os.getenv("PGPORT", 5432)),
        database=os.getenv("PGDATABASE", "crd12"),
        user=os.getenv("PGUSER", "crd_user"),
        password=os.getenv("PGPASSWORD", "crd12")
    )

router = APIRouter(prefix="/api", tags=["roadmap"])

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "crd12_pgvector"),
        port=int(os.getenv("PGPORT", 5432)),
        database=os.getenv("PGDATABASE", "crd12"),
        user=os.getenv("PGUSER", "crd_user"),
        password=os.getenv("PGPASSWORD", "crd12")
    )

@router.get("/roadmap")
async def get_roadmap_json():
    """
    Get full roadmap as JSON
    Returns all tasks from eng_it.roadmap_tasks
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                id, code, title, status, description,
                priority, steps, mechanisms, artifacts,
                created_at, updated_at, completed_at
            FROM eng_it.roadmap_tasks
            ORDER BY priority DESC, code
        """)
        
        tasks = cur.fetchall()
        
        # Convert datetime to ISO format
        for task in tasks:
            if task['created_at']:
                task['created_at'] = task['created_at'].isoformat()
            if task['updated_at']:
                task['updated_at'] = task['updated_at'].isoformat()
            if task['completed_at']:
                task['completed_at'] = task['completed_at'].isoformat()
        
        cur.close()
        conn.close()
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "total_tasks": len(tasks),
            "tasks": tasks
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/truth/matrix")
async def get_truth_matrix():
    """
    Get system truth matrix
    Returns status of all tasks grouped by status
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get task counts by status
        cur.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                json_agg(json_build_object('code', code, 'title', title)) as tasks
            FROM eng_it.roadmap_tasks
            GROUP BY status
            ORDER BY 
                CASE status
                    WHEN 'done' THEN 1
                    WHEN 'in_progress' THEN 2
                    WHEN 'planned' THEN 3
                    WHEN 'blocked' THEN 4
                    ELSE 5
                END
        """)
        
        status_groups = cur.fetchall()
        
        # Get recent events
        cur.execute("""
            SELECT id, ts, source, type, payload
            FROM core.events
            WHERE type LIKE 'roadmap.%'
            ORDER BY ts DESC
            LIMIT 10
        """)
        
        recent_events = cur.fetchall()
        
        # Convert timestamps
        for event in recent_events:
            if event['ts']:
                event['ts'] = event['ts'].isoformat()
        
        cur.close()
        conn.close()
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "matrix": {
                "status_groups": status_groups,
                "recent_events": recent_events
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/current")
async def get_current_task():
    """Get current task from Roadmap (status='in_progress')"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            # Get current task (in_progress with highest priority)
            cursor.execute("""
                SELECT 
                    id,
                    title,
                    status,
                    priority,
                    owner,
                    created_at,
                    updated_at,
                    progress_notes,
                    roadmap_task_id
                FROM eng_it.tasks
                WHERE status = 'in_progress'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """)
            
            task = cursor.fetchone()
            
            if not task:
                # If no in_progress, get first planned task
                cursor.execute("""
                    SELECT 
                        id,
                        title,
                        status,
                        priority,
                        owner,
                        created_at,
                        updated_at,
                        progress_notes,
                        roadmap_task_id
                    FROM eng_it.tasks
                    WHERE status = 'planned'
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """)
                task = cursor.fetchone()
            
            if not task:
                return JSONResponse(content={
                    "status": "error",
                    "message": "No current or planned tasks found",
                    "task": None
                })
            
            # Convert datetime objects to strings
            task_dict = dict(task)
            for key, value in task_dict.items():
                if hasattr(value, 'isoformat'):
                    task_dict[key] = value.isoformat()
            
            return JSONResponse(content={
                "status": "ok",
                "task": task_dict,
                "timestamp": "2025-11-19T09:27:40Z"
            })
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
