import requests
import json

def test_all_endpoints():
    print("=== ТЕСТ СИСТЕМЫ СВОДКИ ВНУТРИ КОНТЕЙНЕРА ===")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/health",
        "/test", 
        "/system/status",
        "/system/summary"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint}: Работает")
                
                if endpoint == "/system/status":
                    data = response.json()
                    print(f"   Система: {data['system']}")
                    print(f"   Stage: {data['stage']}")
                    print(f"   БД: {data['database']['status']}")
                    print(f"   Jobs: {data['database']['jobs_count']}")
                    print(f"   Events: {data['database']['events_count']}")
                    
                elif endpoint == "/system/summary":
                    data = response.json()
                    print(f"   Кратко: {data['system']} - {data['stage']}")
                    
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

if __name__ == "__main__":
    test_all_endpoints()
