import requests
import time

def simple_availability_test():
    print("Простой тест доступности сервиса:")
    
    # Тестируем разные порты
    ports = [8030, 8000, 8001]
    
    for port in ports:
        try:
            url = f"http://localhost:{port}/health"
            response = requests.get(url, timeout=3)
            print(f"✅ Порт {port}: {response.status_code} - {response.json()}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Порт {port}: Connection refused")
        except Exception as e:
            print(f"❌ Порт {port}: {e}")
    
    # Тестируем Jobs API на рабочем порту
    working_port = 8030
    endpoints = [
        "/api/v1/jobs/test",
        "/api/v1/jobs/list", 
        "/api/v1/jobs/create"
    ]
    
    print(f"\nТестируем Jobs API на порту {working_port}:")
    for endpoint in endpoints:
        try:
            url = f"http://localhost:{working_port}{endpoint}"
            if endpoint == "/api/v1/jobs/create":
                response = requests.post(url, json={"source": "port_test", "task_type": "test"}, timeout=5)
            else:
                response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: {response.status_code}")
            else:
                print(f"❌ {endpoint}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

if __name__ == "__main__":
    simple_availability_test()
