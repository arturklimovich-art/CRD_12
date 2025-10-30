from fastapi import APIRouter
import requests
import psycopg2
import os

router = APIRouter()

@router.get("/smoke/run")
async def run_smoke_test():
    """Упрощенный smoke test"""
    results = {}
    
    # Проверка API
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        results["api_health"] = response.status_code == 200
    except:
        results["api_health"] = False
    
    # Проверка БД
    try:
        conn = psycopg2.connect(
            host="pgvector", database="crd12", 
            user="crd_user", password="crd12", port="5432"
        )
        conn.close()
        results["database"] = True
    except:
        results["database"] = False
    
    # Проверка файлов
    results["files"] = {
        "app.py": os.path.exists("/app/app.py"),
        "marker_selfbuild.py": os.path.exists("/app/marker_selfbuild.py")
    }
    
    all_ok = all([
        results["api_health"],
        results["database"],
        all(results["files"].values())
    ])
    
    # Логируем в Events Service
    try:
        event_type = "SMOKE_OK" if all_ok else "SMOKE_FAILED"
        requests.post(
            "http://events_service:8031/events/log",
            json={
                "source": "smoke_test",
                "type": event_type,
                "payload": results
            },
            timeout=2
        )
    except:
        pass
    
    return {
        "status": "success" if all_ok else "failed",
        "results": results,
        "all_tests_passed": all_ok
    }
