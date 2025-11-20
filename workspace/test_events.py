import sys
sys.path.insert(0, r"C:\Users\Artur\Documents\CRD12\src\app\engineer_b_api")
from events import send_system_event

# Тест логирования события
send_system_event(
    event_type="llm.test",
    payload={"test": "event_logging_works", "timestamp": "2025-11-17T16:57:08Z"},
    source="test_script"
)
print("✅ Test event sent successfully")
