import requests
import json

def test_status_endpoints():
    print("=== ТЕСТ СИСТЕМЫ СВОДКИ СОСТОЯНИЯ ===")
    
    try:
        # Полная сводка
        response = requests.get("http://localhost:8000/system/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("✅ /system/status: Работает")
            print(f"   Общее состояние: {status['system_health']}")
            print(f"   Завершение Stage-1: {status['completion_percentage']}%")
            print(f"   Jobs в БД: {status['components']['database']['jobs_total']}")
            print(f"   Событий в БД: {status['components']['database']['events_total']}")
        else:
            print(f"❌ /system/status: {response.status_code}")
    except Exception as e:
        print(f"❌ /system/status: {e}")
    
    try:
        # Краткая сводка
        response = requests.get("http://localhost:8000/system/summary", timeout=10)
        if response.status_code == 200:
            summary = response.json()
            print("✅ /system/summary: Работает")
            print(f"   Компоненты: {json.dumps(summary['components'], indent=2)}")
        else:
            print(f"❌ /system/summary: {response.status_code}")
    except Exception as e:
        print(f"❌ /system/summary: {e}")

if __name__ == "__main__":
    test_status_endpoints()
