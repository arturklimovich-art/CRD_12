#!/usr/bin/env python3
import requests
import json

print("Отправка тестового запроса в Engineer B API...")

payload = {
    "task": "Test: create hello() function",
    "job_id": "test-12345"
}

try:
    response = requests.post(
        "http://engineer_b_api:8000/agent/analyze",
        json=payload,
        timeout=120
    )
    
    print(f"\n✅ HTTP Status: {response.status_code}\n")
    
    result = response.json()
    
    print("=" * 60)
    print("ПОЛНЫЙ ОТВЕТ ОТ ENGINEER B:")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
    print("=" * 60)
    
    print("\n📋 ДОСТУПНЫЕ КЛЮЧИ В ОТВЕТЕ:")
    print(list(result.keys()))
    
    print("\n🔍 ПОИСК КЛЮЧА СО СТАТУСОМ:")
    for key in ["status", "engineer_status", "result", "state", "analysis_status"]:
        if key in result:
            print(f"  ✅ Найден ключ '{key}': {result[key]}")
    
    print("\n🔍 ПОИСК КЛЮЧА С КОДОМ:")
    for key in ["generated_code", "code", "solution", "result_code"]:
        if key in result:
            code_len = len(result[key]) if result[key] else 0
            print(f"  ✅ Найден ключ '{key}': {code_len} символов")
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
