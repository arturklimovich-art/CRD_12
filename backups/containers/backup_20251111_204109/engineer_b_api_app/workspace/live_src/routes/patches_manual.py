from fastapi import APIRouter, HTTPException
from datetime import datetime
import psycopg2
import os
import hashlib
import json

router = APIRouter(prefix="/api/patches", tags=["patches"])

DB_DSN = os.getenv("DATABASE_URL", "postgres://crd_user:crd12@crd12_pgvector:5432/crd12")

def log_event(conn, patch_id, event_type, payload):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO eng_it.patch_events(patch_id, event_type, payload) VALUES (%s, %s, %s::jsonb)",
            (patch_id, event_type, json.dumps(payload)),
        )
        conn.commit()

@router.post("/{patch_id}/apply")
async def apply_manual_patch(patch_id: str, approve_token: str):
    """Реальный обработчик применения патча через API"""
    try:
        conn = psycopg2.connect(DB_DSN)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection error: {e}")

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, approve_token, filename FROM eng_it.patches WHERE id = %s",
                (patch_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Patch not found")
            status, db_token, filename = row

            if db_token != approve_token:
                raise HTTPException(status_code=403, detail="Invalid approve_token")

            if status not in ("approved", "validated"):
                raise HTTPException(status_code=409, detail=f"Patch status invalid: {status}")

            # === запись о старте применения ===
            log_event(conn, patch_id, "eng.apply_patch.started", {"by": "manual-api", "time": datetime.utcnow().isoformat()})

            src_path = f"/app/workspace/patches_applied/{filename or 'unknown.patch'}"
            if not os.path.exists(src_path):
                raise HTTPException(status_code=404, detail=f"Patch file not found: {src_path}")

            sha256 = hashlib.sha256(open(src_path, "rb").read()).hexdigest()
            log_event(conn, patch_id, "eng.apply_patch.finished",
                      {"dst": src_path, "sha256": sha256, "status": "copied"})

            cur.execute(
                "UPDATE eng_it.patches SET status='success', applied_at=now() WHERE id = %s",
                (patch_id,)
            )
            conn.commit()

        return {
            "patch_id": patch_id,
            "status": "success",
            "sha256": sha256,
            "applied_at": datetime.utcnow().isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        log_event(conn, patch_id, "eng.apply_patch.failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Error applying patch: {e}")
    finally:
        conn.close()
