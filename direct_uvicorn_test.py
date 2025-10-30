import subprocess
import time
import requests
import sys
import os

def test_direct_uvicorn():
    print("=== ПРЯМОЙ ТЕСТ UVICORN ===")
    
    # Запускаем uvicorn напрямую в фоновом режиме
    uvicorn_cmd = [sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
    process = subprocess.Popen(uvicorn_cmd, cwd="/app", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Даем время на запуск
    time.sleep(3)
    
    # Тестируем прямой порт 8001
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        print(f"✅ Прямой порт 8001: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Прямой порт 8001: {e}")
    
    # Тестируем порт supervisor 8030
    try:
        response = requests.get("http://localhost:8030/health", timeout=5)
        print(f"✅ Supervisor порт 8030: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Supervisor порт 8030: {e}")
    
    # Тестируем другие эндпоинты на прямом порту
    endpoints = ["/test", "/openapi.json"]
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8001{endpoint}", timeout=5)
            print(f"✅ 8001{endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ 8001{endpoint}: {e}")
    
    # Завершаем процесс
    process.terminate()
    process.wait()

if __name__ == "__main__":
    test_direct_uvicorn()
