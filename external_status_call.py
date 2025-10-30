import requests
import json
import sys

def get_system_status_external():
    """Получает сводку состояния системы через внутренний вызов"""
    try:
        # Вызываем внутренний эндпоинт
        response = requests.get("http://localhost:8000/system/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            
            print("🎯 СВОДКА СОСТОЯНИЯ СИСТЕМЫ ENGINEERS_IT CORE")
            print("=" * 50)
            print(f"Система: {status['system']}")
            print(f"Stage: {status['stage']}")
            print(f"Версия: {status['version']}")
            print(f"Время: {status['timestamp']}")
            print(f"Состояние БД: {status['database']['status']}")
            print(f"Всего заданий: {status['database']['jobs_count']}")
            print(f"Всего событий: {status['database']['events_count']}")
            print("")
            print("📊 События по типам:")
            for event_type, count in status['database']['events_by_type'].items():
                print(f"  {event_type}: {count}")
            print("")
            print("📁 Критические файлы:")
            for file, exists in status['filesystem']['critical_files'].items():
                status_icon = "✅" if exists else "❌"
                print(f"  {status_icon} {file}")
            print("")
            print("🔧 Marker Selfbuild:")
            print(f"  {status['filesystem']['marker_content']}")
            print("=" * 50)
            
            return True
        else:
            print(f"❌ Ошибка получения сводки: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = get_system_status_external()
    sys.exit(0 if success else 1)
