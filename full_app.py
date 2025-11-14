from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import psycopg2
import os
import uvicorn

app = FastAPI(title="Engineer B API", version="4.1")

def get_db_connection():
    try:
        conn = psycopg2.connect("postgres://crd_user:crd12@crd12_pgvector:5432/crd12")
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.get("/roadmap")
async def get_roadmap():
    conn = get_db_connection()
    if not conn:
        return JSONResponse(
            status_code=500,
            content={"error": "Database connection failed"}
        )
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, title, status FROM eng_it.tasks ORDER BY created_at DESC LIMIT 50")
        tasks = []
        for row in cur.fetchall():
            tasks.append({
                "id": row[0],
                "title": row[1],
                "status": row[2]
            })
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Database query failed: {str(e)}"}
        )

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Engineer B API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
