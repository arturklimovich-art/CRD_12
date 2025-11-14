"""
Roadmap API Router
Uses psycopg2 for proper UTF-8 handling
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any

router = APIRouter(prefix="/api/v1/roadmap", tags=["roadmap"])

def get_connection():
    """Get database connection with proper encoding"""
    return psycopg2.connect(
        host="crd12_pgvector",
        port=5432,
        user="crd_user",
        password="crd_password",
        database="crd12",
        client_encoding='UTF8'
    )

@router.get("/dashboard")
async def get_dashboard():
    """Get dashboard summary data"""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            # Get statistics
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT block_code) as total_blocks,
                    COUNT(*) as total_tasks,
                    COUNT(*) FILTER (WHERE status = 'done') as total_done,
                    ROUND(
                        COUNT(*) FILTER (WHERE status = 'done')::numeric / 
                        NULLIF(COUNT(*), 0)::numeric * 100, 
                        2
                    ) as overall_completion
                FROM eng_it.roadmap_tasks
            """)
            stats = cursor.fetchone()
            
            # Get blocks with completion
            cursor.execute("""
                SELECT 
                    block_code,
                    block_title,
                    block_status,
                    COUNT(*) as tasks_total,
                    COUNT(*) FILTER (WHERE status = 'done') as tasks_done,
                    ROUND(
                        COUNT(*) FILTER (WHERE status = 'done')::numeric / 
                        COUNT(*)::numeric * 100, 
                        1
                    ) as completion_percentage
                FROM eng_it.roadmap_tasks
                GROUP BY block_code, block_title, block_status
                ORDER BY block_code
            """)
            blocks = cursor.fetchall()
            
            result = {
                "total_blocks": stats['total_blocks'],
                "total_tasks": stats['total_tasks'],
                "total_done": stats['total_done'],
                "overall_completion": float(stats['overall_completion'] or 0),
                "blocks": [dict(row) for row in blocks]
            }
            
            return JSONResponse(
                content=result,
                media_type="application/json; charset=utf-8"
            )
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/tasks")
async def get_tasks(limit: int = 10):
    """Get recent tasks"""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT 
                    code, 
                    title, 
                    status, 
                    block_code
                FROM eng_it.roadmap_tasks
                ORDER BY 
                    CASE status
                        WHEN 'done' THEN 1
                        WHEN 'in_progress' THEN 2
                        WHEN 'planned' THEN 3
                        ELSE 4
                    END,
                    code
                LIMIT %s
            """, (limit,))
            
            tasks = cursor.fetchall()
            result = [dict(row) for row in tasks]
            
            return JSONResponse(
                content=result,
                media_type="application/json; charset=utf-8"
            )
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")