from fastapi import FastAPI
import uvicorn
import psycopg2
import os
from datetime import datetime

app = FastAPI(title="Engineer_B_API_With_Status")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "with_status"}

# Простая сводка состояния - встроенная в app.py
@app.get("/system/status")
async def system_status():
    """Простая сводка состояния системы"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "system": "Engineers_IT Core",
        "stage": "Stage-1 Completed", 
        "version": "v1.1",
        "health": "healthy"
    }
    
    # Проверка базы данных
    try:
        conn = psycopg2.connect(
            host="pgvector", database="crd12",
            user="crd_user", password="crd12", port="5432"
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM core.jobs")
        jobs_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM core.events") 
        events_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT type, COUNT(*) FROM core.events GROUP BY type")
        events_by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        status["database"] = {
            "status": "healthy",
            "jobs_count": jobs_count,
            "events_count": events_count,
            "events_by_type": events_by_type
        }
        
        cursor.close()
        conn.close()
    except Exception as e:
        status["database"] = {"status": "error", "error": str(e)}
    
    # Проверка файлов
    critical_files = {
        "app.py": os.path.exists("/app/app.py"),
        "marker_selfbuild.py": os.path.exists("/app/marker_selfbuild.py")
    }
    
    marker_content = ""
    if critical_files["marker_selfbuild.py"]:
        with open("/app/marker_selfbuild.py", "r") as f:
            marker_content = f.read().strip()
    
    status["filesystem"] = {
        "critical_files": critical_files,
        "marker_content": marker_content
    }
    
    return status

@app.get("/system/summary")
async def system_summary():
    """Краткая сводка"""
    full_status = await system_status()
    
    return {
        "timestamp": full_status["timestamp"],
        "system": full_status["system"],
        "stage": full_status["stage"],
        "database_health": full_status["database"]["status"],
        "jobs_count": full_status["database"]["jobs_count"],
        "events_count": full_status["database"]["events_count"]
    }

# Добавляем тестовый эндпоинт для проверки
@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint works"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
