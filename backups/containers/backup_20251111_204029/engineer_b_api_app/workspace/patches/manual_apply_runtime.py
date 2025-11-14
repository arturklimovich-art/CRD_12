import psycopg2, json, os, hashlib, datetime, sys

PATCH_ID = "f46262d1-ff1d-4612-909e-939b607b149a"
APPROVE_TOKEN = "manual-token-123"
DST_DIR = "/app/workspace/patches_applied"

def log_event(conn, patch_id, event_type, payload):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO eng_it.patch_events (patch_id, event_type, payload) VALUES (%s,%s,%s::jsonb)",
            (patch_id, event_type, json.dumps(payload))
        )
    conn.commit()

def main():
    try:
        conn = psycopg2.connect("dbname=crd12 user=crd_user password=crd12 host=crd12_pgvector port=5432")
    except Exception as e:
        print("DB connect error:", e)
        sys.exit(1)

    cur = conn.cursor()
    cur.execute("SELECT id, approve_token, status, filename, content FROM eng_it.patches WHERE id=%s", (PATCH_ID,))
    row = cur.fetchone()
    if not row:
        print("❌ Patch not found"); return
    pid, db_token, db_status, fname, content = row
    if db_status != "approved":
        print(f"❌ Patch not approved (status={db_status})"); return
    if db_token and db_token != APPROVE_TOKEN:
        print("❌ Approve token mismatch"); return

    log_event(conn, pid, "eng.apply_patch.started", {"by":"Invoke-ManualPatchApply.ps1","time":datetime.datetime.utcnow().isoformat()})
    os.makedirs(DST_DIR, exist_ok=True)
    dst_file = os.path.join(DST_DIR, fname)
    with open(dst_file, "wb") as f:
        f.write(content)
    sha = hashlib.sha256(content).hexdigest()
    log_event(conn, pid, "eng.apply_patch.finished", {"sha256":sha,"dst":dst_file,"status":"copied"})
    print(f"✅ Patch {pid} applied -> {dst_file}, sha={sha}")

if __name__ == "__main__":
    main()
