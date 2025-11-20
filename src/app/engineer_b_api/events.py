# src/app/engineer_b_api/events.py
import psycopg2
import json
import logging
from datetime import datetime

log = logging.getLogger(__name__)

def send_system_event(event_type: str, payload: dict, source: str = "engineer_b", job_id: str = None):
    """
    Отправка системного события в core.events
    
    Args:
        event_type: Тип события (например, 'llm.request', 'llm.response')
        payload: JSON-совместимый словарь с данными события
        source: Источник события (по умолчанию 'engineer_b')
        job_id: Опциональный идентификатор задачи
    """
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="crd12",
            user="crd_user",
            password="crd12"
        )
        cursor = conn.cursor()
        
        query = """
        INSERT INTO core.events (source, type, payload, job_id)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (source, event_type, json.dumps(payload), job_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        log.info(f"Event logged: {event_type} from {source}")
    except Exception as e:
        log.error(f"Failed to log event {event_type}: {e}")
        print(f"SYSTEM EVENT (fallback): {event_type} - {payload}")
