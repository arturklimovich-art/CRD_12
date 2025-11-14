# core/event_bus.py
from __future__ import annotations
import os, json, uuid, time, datetime as dt, hashlib, io
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Env
DATABASE_URL = os.getenv("DATABASE_URL", "")
S3_ENDPOINT   = os.getenv("S3_ENDPOINT", "")
S3_BUCKET     = os.getenv("S3_BUCKET", "")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_SECURE     = os.getenv("S3_SECURE", "1") in ("1", "true", "True")
EVENT_SINK    = os.getenv("EVENT_SINK", "auto")  # auto|db|log
SERVICE_NAME  = "engineer_b_api"

_psycopg = None
_boto3   = None

try:
    import psycopg
    _psycopg = psycopg
except Exception:
    pass

try:
    import boto3
    _boto3 = boto3
except Exception:
    pass


def _now_iso() -> str:
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()

def ensure_events_table():
    if not _psycopg or not DATABASE_URL:
        return
    try:
        with _psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                create table if not exists core_events (
                  id uuid primary key,
                  ts_utc timestamptz not null,
                  service text not null,
                  stage text not null,
                  event_type text not null,
                  job_id text,
                  idempotency_key text,
                  context jsonb
                );
                """)
            conn.commit()
    except Exception as e:
        logger.warning("events: failed to ensure table: %s", e)

def put_event(stage: str, event_type: str, context: Dict[str, Any],
              job_id: Optional[str]=None, idempotency_key: Optional[str]=None) -> str:
    """
    Пишет событие в БД, либо в лог (fallback). Возвращает event_id.
    """
    event = {
        "id": str(uuid.uuid4()),
        "ts_utc": _now_iso(),
        "service": SERVICE_NAME,
        "stage": stage,
        "event_type": event_type,
        "job_id": job_id,
        "idempotency_key": idempotency_key,
        "context": context or {},
    }

    # DB sink
    if (EVENT_SINK in ("db", "auto")) and _psycopg and DATABASE_URL:
        try:
            with _psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                    insert into core_events (id, ts_utc, service, stage, event_type, job_id, idempotency_key, context)
                    values (%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        event["id"], event["ts_utc"], event["service"], event["stage"],
                        event["event_type"], event["job_id"], event["idempotency_key"],
                        json.dumps(event["context"], ensure_ascii=False),
                    ))
                conn.commit()
            return event["id"]
        except Exception as e:
            logger.warning("events: db insert failed, fallback to log: %s", e)

    # Log sink (structured)
    logger.info("EVENT %s", json.dumps(event, ensure_ascii=False))
    return event["id"]

def upload_artifact(key: str, bytes_data: bytes, content_type: str="text/plain") -> Optional[str]:
    """
    Загружает артефакт в S3/MinIO. Возвращает s3://bucket/key либо None.
    """
    if not _boto3 or not S3_BUCKET or not S3_ENDPOINT:
        logger.info("artifacts: S3 not configured; skip upload key=%s", key)
        return None
    try:
        s3 = _boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY or None,
            aws_secret_access_key=S3_SECRET_KEY or None,
            use_ssl=S3_SECURE,
        )
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=bytes_data, ContentType=content_type)
        return f"s3://{S3_BUCKET}/{key}"
    except Exception as e:
        logger.warning("artifacts: upload failed key=%s err=%s", key, e)
        return None
