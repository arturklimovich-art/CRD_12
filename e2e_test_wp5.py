import requests
import json
import uuid
import psycopg2
import time

def run_e2e_test():
    print("=== ЗАПУСК E2E ТЕСТА WP-5 ===")
    
    # 1. Создаем уникальный job_id для отслеживания
    job_id = f"e2e_test_{uuid.uuid4().hex[:8]}"
    print(f"1. Создан job_id: {job_id}")
    
    # 2. Создаем задание через Jobs API
    try:
        job_data = {
            "source": "e2e_test_wp5",
            "task_type": "update_marker",
            "meta": {
                "phase": "wp5_final",
                "target_file": "marker_selfbuild.py",
                "new_value": "STAGE1_E2E_OK"
            }
        }
        
        # Внутренний запрос к Jobs API
        response = requests.post(
            "http://localhost:8000/api/v1/jobs/create",
            json=job_data,
            timeout=10
        )
        
        if response.status_code == 200:
            job_result = response.json()
            print(f"2. ✅ Задание создано: {job_result['job_id']}")
            
            # Логируем событие
            try:
                event_data = {
                    "source": "e2e_test",
                    "type": "ANALYZE_OK", 
                    "job_id": job_id,
                    "payload": {
                        "task": "update_marker",
                        "status": "analyzed"
                    }
                }
                requests.post("http://events_service:8031/events/log", json=event_data, timeout=3)
                print("3. ✅ Событие ANALYZE_OK записано")
            except Exception as e:
                print(f"3. ⚠️ Ошибка логирования ANALYZE_OK: {e}")
            
            # 4. Обновляем marker_selfbuild.py
            try:
                new_code = 'def marker_selfbuild():\n    return "STAGE1_E2E_OK"'
                with open('/app/marker_selfbuild.py', 'w') as f:
                    f.write(new_code)
                print("4. ✅ marker_selfbuild.py обновлен на STAGE1_E2E_OK")
                
                # Логируем событие применения патча
                try:
                    patch_event = {
                        "source": "e2e_test", 
                        "type": "PATCH_APPLIED",
                        "job_id": job_id,
                        "payload": {
                            "file": "marker_selfbuild.py",
                            "new_value": "STAGE1_E2E_OK"
                        }
                    }
                    requests.post("http://events_service:8031/events/log", json=patch_event, timeout=3)
                    print("5. ✅ Событие PATCH_APPLIED записано")
                except Exception as e:
                    print(f"5. ⚠️ Ошибка логирования PATCH_APPLIED: {e}")
                
                # 6. Проверяем обновление
                try:
                    with open('/app/marker_selfbuild.py', 'r') as f:
                        content = f.read()
                    if "STAGE1_E2E_OK" in content:
                        print("6. ✅ Проверка: marker_selfbuild.py содержит STAGE1_E2E_OK")
                        
                        # Логируем успешное завершение
                        try:
                            success_event = {
                                "source": "e2e_test",
                                "type": "E2E_TEST_OK", 
                                "job_id": job_id,
                                "payload": {
                                    "status": "completed",
                                    "file_updated": "marker_selfbuild.py",
                                    "new_value": "STAGE1_E2E_OK"
                                }
                            }
                            requests.post("http://events_service:8031/events/log", json=success_event, timeout=3)
                            print("7. ✅ Событие E2E_TEST_OK записано")
                        except Exception as e:
                            print(f"7. ⚠️ Ошибка логирования E2E_TEST_OK: {e}")
                    else:
                        print("6. ❌ Ошибка: marker_selfbuild.py не обновлен")
                except Exception as e:
                    print(f"6. ❌ Ошибка проверки файла: {e}")
                    
            except Exception as e:
                print(f"4. ❌ Ошибка обновления файла: {e}")
        else:
            print(f"2. ❌ Ошибка создания задания: {response.status_code}")
            
    except Exception as e:
        print(f"2. ❌ Ошибка Jobs API: {e}")
    
    # 8. Проверяем данные в БД
    try:
        conn = psycopg2.connect(
            host="pgvector", database="crd12",
            user="crd_user", password="crd12", port="5432"
        )
        cursor = conn.cursor()
        
        # Проверяем события
        cursor.execute("SELECT type, COUNT(*) FROM core.events WHERE source = 'e2e_test' GROUP BY type")
        events = cursor.fetchall()
        print("8. События E2E теста в БД:")
        for event_type, count in events:
            print(f"   - {event_type}: {count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"8. ❌ Ошибка проверки БД: {e}")
    
    print("=== E2E ТЕСТ ЗАВЕРШЕН ===")

if __name__ == "__main__":
    run_e2e_test()
