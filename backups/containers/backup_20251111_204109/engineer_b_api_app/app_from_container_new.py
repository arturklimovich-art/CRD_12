from subprocess import Popen, PIPE
from fastapi import Body

@app.post("/api/patches/{patch_id}/apply")
async def apply_manual_patch_inline(patch_id: str, approve_token: str = Body(None)):
    # читаем патч из БД
    get_patch_sql = f"SELECT id, approve_token, status FROM eng_it.patches WHERE id = ''{patch_id}'' LIMIT 1;"
    proc = Popen([
        "psql", "-U", "crd_user", "-d", "crd12",
        "-t", "-A", "-c", get_patch_sql
    ], stdout=PIPE, stderr=PIPE, text=True)
    out, err = proc.communicate(timeout=5)

    if proc.returncode != 0:
        return {"patch_id": patch_id, "status": "db_error", "error": err.strip(), "source": "app.py"}

    line = out.strip()
    if not line:
        return {"patch_id": patch_id, "status": "not_found", "source": "app.py"}

    parts = line.split("|")
    db_id = parts[0]
    db_token = parts[1] if len(parts) > 1 else ""
    db_status = parts[2] if len(parts) > 2 else ""

    if db_status != "approved":
        return {"patch_id": patch_id, "status": "rejected", "reason": f"status={db_status}", "source": "app.py"}

    if db_token and approve_token != db_token:
        return {"patch_id": patch_id, "status": "rejected", "reason": "approve_token mismatch", "source": "app.py"}

    # пишем события
    start_sql = f"INSERT INTO eng_it.patch_events (patch_id, event_type, payload) VALUES (''{patch_id}'',''eng.apply_patch.started'',''{{\"by\":\"engineer_b_api\"}}''::jsonb);"
    Popen(["psql","-U","crd_user","-d","crd12","-c", start_sql], stdout=PIPE, stderr=PIPE, text=True).communicate()

    done_sql = f"INSERT INTO eng_it.patch_events (patch_id, event_type, payload) VALUES (''{patch_id}'',''eng.apply_patch.finished'',''{{\"result\":\"simulated\"}}''::jsonb);"
    Popen(["psql","-U","crd_user","-d","crd12","-c", done_sql], stdout=PIPE, stderr=PIPE, text=True).communicate()

    return {"patch_id": patch_id, "status": "apply_simulated", "source": "app.py"}
