from fastapi import APIRouter
import psycopg2
import requests
import os
import subprocess
from datetime import datetime

router = APIRouter()

async def get_system_status():
    """Генерирует полную сводку состояния системы"""
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "system": "Engineers_IT Core",
        "stage": "Stage-1 Completed",
        "version": "v1.1",
        "components": {}
    }
    
    # 1. Проверка базы данных
    try:
        conn = psycopg2.connect(
            host="pgvector", database="crd12",
            user="crd_user", password="crd12", port="5432"
        )
        cursor = conn.cursor()
        
        # Статистика jobs
        cursor.execute("SELECT status, COUNT(*) FROM core.jobs GROUP BY status")
        jobs_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Статистика events
        cursor.execute("SELECT type, COUNT(*) FROM core.events GROUP BY type")
        events_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Последние события
        cursor.execute("""
            SELECT type, source, ts::text 
            FROM core.events 
            ORDER BY ts DESC 
            LIMIT 5
        """)
        recent_events = [
            {"type": row[0], "source": row[1], "timestamp": row[2]}
            for row in cursor.fetchall()
        ]
        
        status["components"]["database"] = {
            "status": "healthy",
            "jobs_total": sum(jobs_stats.values()),
            "jobs_by_status": jobs_stats,
            "events_total": sum(events_stats.values()),
            "events_by_type": events_stats,
            "recent_events": recent_events
        }
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        status["components"]["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # 2. Проверка файловой системы
    try:
        critical_files = {
            "app.py": os.path.exists("/app/app.py"),
            "marker_selfbuild.py": os.path.exists("/app/marker_selfbuild.py"),
            "jobs_ultra_simple.py": os.path.exists("/app/jobs_ultra_simple.py"),
            "smoke_test.py": os.path.exists("/app/smoke_test.py")
        }
        
        # Проверяем содержимое marker_selfbuild
        marker_content = ""
        if critical_files["marker_selfbuild.py"]:
            with open("/app/marker_selfbuild.py", "r") as f:
                marker_content = f.read().strip()
        
        status["components"]["filesystem"] = {
            "status": "healthy" if all(critical_files.values()) else "degraded",
            "critical_files": critical_files,
            "marker_selfbuild_content": marker_content
        }
        
    except Exception as e:
        status["components"]["filesystem"] = {
            "status": "error", 
            "error": str(e)
        }
    
    # 3. Проверка сервисов
    services_status = {}
    
    # Проверка Engineer_B API
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        services_status["engineer_b_api"] = {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "port_8000": response.status_code == 200
        }
    except:
        services_status["engineer_b_api"] = {"status": "unhealthy", "port_8000": False}
    
    # Проверка Events Service
    try:
        response = requests.get("http://events_service:8031/events", timeout=3)
        services_status["events_service"] = {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "port_8031": response.status_code == 200
        }
    except:
        services_status["events_service"] = {"status": "unhealthy", "port_8031": False}
    
    # Проверка DeepSeek Proxy
    try:
        response = requests.get("http://deepseek_proxy:8010/health", timeout=3)
        services_status["deepseek_proxy"] = {
            "status": "healthy" if response.status_code == 200 else "unhealthy", 
            "port_8010": response.status_code == 200
        }
    except:
        services_status["deepseek_proxy"] = {"status": "unhealthy", "port_8010": False}
    
    status["components"]["services"] = services_status
    
    # 4. Общая оценка состояния системы
    all_healthy = all(
        comp["status"] == "healthy" 
        for comp in status["components"].values() 
        if "status" in comp
    )
    
    status["system_health"] = "healthy" if all_healthy else "degraded"
    status["completion_percentage"] = 100  # Stage-1 completed
    
    return status

@router.get("/system/status")
async def system_status():
    """Возвращает полную сводку состояния системы"""
    return await get_system_status()

@router.get("/system/summary")
async def system_summary():
    """Краткая сводка состояния системы"""
    full_status = await get_system_status()
    
    summary = {
        "timestamp": full_status["timestamp"],
        "system_health": full_status["system_health"],
        "completion_percentage": full_status["completion_percentage"],
        "components": {
            name: comp["status"] 
            for name, comp in full_status["components"].items()
            if "status" in comp
        },
        "database_stats": {
            "jobs_total": full_status["components"]["database"].get("jobs_total", 0),
            "events_total": full_status["components"]["database"].get("events_total", 0)
        }
    }
    
    return summary
