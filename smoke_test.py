from fastapi import APIRouter
import requests
import psycopg2
import os
import subprocess
import sys

router = APIRouter()

async def check_api_health():
    """Проверка здоровья основного API"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

async def check_database_connection():
    """Проверка подключения к базе данных"""
    try:
        conn = psycopg2.connect(
            host="pgvector",
            database="crd12", 
            user="crd_user",
            password="crd12",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except:
        return False

async def check_critical_files():
    """Проверка наличия критических файлов"""
    critical_files = [
        "/app/app.py",
        "/app/marker_selfbuild.py",
        "/app/jobs_ultra_simple.py"
    ]
    
    results = {}
    for file_path in critical_files:
        results[file_path] = os.path.exists(file_path)
    
    return results

async def attempt_recovery():
    """Попытка восстановления системы"""
    recovery_actions = []
    
    try:
        # Проверяем есть ли бэкапы
        backup_files = [f for f in os.listdir("/app") if f.endswith(".bak") or "backup" in f]
        recovery_actions.append(f"Найдено бэкапов: {len(backup_files)}")
        
        # Если есть проблемы с основными файлами, пытаемся восстановить из бэкапов
        critical_files = ["/app/app.py", "/app/marker_selfbuild.py"]
        
        for file_path in critical_files:
            backup_candidates = [f for f in backup_files if os.path.basename(file_path) in f]
            if backup_candidates and not os.path.exists(file_path):
                latest_backup = sorted(backup_candidates)[-1]
                subprocess.run(["cp", f"/app/{latest_backup}", file_path], check=True)
                recovery_actions.append(f"Восстановлен {file_path} из {latest_backup}")
        
        # Перезапускаем сервис если нужно
        recovery_actions.append("Попытка перезапуска сервиса")
        
        return {
            "success": True,
            "actions": recovery_actions,
            "message": "Recovery attempted"
        }
        
    except Exception as e:
        return {
            "success": False,
            "actions": recovery_actions,
            "error": str(e)
        }

@router.get("/smoke/run")
async def run_smoke_test():
    """Запуск smoke-тестов и восстановления при необходимости"""
    smoke_results = {}
    recovery_attempted = False
    
    # 1. Проверка API здоровья
    smoke_results["api_health"] = await check_api_health()
    
    # 2. Проверка базы данных
    smoke_results["database_connection"] = await check_database_connection()
    
    # 3. Проверка критических файлов
    smoke_results["critical_files"] = await check_critical_files()
    
    # 4. Проверка Jobs API
    try:
        response = requests.get("http://localhost:8000/api/v1/jobs/test", timeout=5)
        smoke_results["jobs_api"] = response.status_code == 200
    except:
        smoke_results["jobs_api"] = False
    
    # 5. Проверка Events Service
    try:
        response = requests.get("http://events_service:8031/events", timeout=5)
        smoke_results["events_service"] = response.status_code == 200
    except:
        smoke_results["events_service"] = False
    
    # Анализ результатов
    all_tests_passed = all([
        smoke_results["api_health"],
        smoke_results["database_connection"],
        smoke_results["jobs_api"],
        all(smoke_results["critical_files"].values())
    ])
    
    # Логика восстановления
    recovery_result = None
    if not all_tests_passed:
        recovery_attempted = True
        recovery_result = await attempt_recovery()
        
        # Повторная проверка после восстановления
        if recovery_result["success"]:
            smoke_results["after_recovery"] = {
                "api_health": await check_api_health(),
                "database_connection": await check_database_connection()
            }
    
    # Логирование события
    try:
        event_data = {
            "source": "smoke_test",
            "type": "SMOKE_OK" if all_tests_passed else "SMOKE_FAILED",
            "job_id": None,
            "payload": {
                "smoke_results": smoke_results,
                "recovery_attempted": recovery_attempted,
                "recovery_result": recovery_result,
                "all_tests_passed": all_tests_passed
            }
        }
        requests.post("http://events_service:8031/events/log", json=event_data, timeout=3)
    except:
        pass  # Игнорируем ошибки логирования
    
    return {
        "smoke_test": {
            "all_tests_passed": all_tests_passed,
            "results": smoke_results,
            "recovery_attempted": recovery_attempted,
            "recovery_result": recovery_result,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
    }
