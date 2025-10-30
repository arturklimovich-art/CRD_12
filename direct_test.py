import requests
import sys

base_url = "http://localhost:8030"
endpoints = [
    "/health",
    "/api/v1/jobs/test", 
    "/api/v1/jobs/create",
    "/api/v1/jobs/list",
    "/debug/routes"
]

print("Прямой тест эндпоинтов через requests:")
for endpoint in endpoints:
    try:
        if endpoint == "/api/v1/jobs/create":
            # POST запрос для создания задания
            response = requests.post(
                f"{base_url}{endpoint}",
                json={"source": "direct_test", "task_type": "diagnostic"},
                timeout=5
            )
        else:
            # GET запросы для остальных эндпоинтов
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
        
        print(f"  {endpoint}: {response.status_code}")
        if response.status_code == 200:
            print(f"    Response: {response.json()}")
    except Exception as e:
        print(f"  {endpoint}: ERROR - {e}")
