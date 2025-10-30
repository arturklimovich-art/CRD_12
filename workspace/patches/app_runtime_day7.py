from fastapi import FastAPI, Body, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
import json, urllib.request

from agents.self_healing import SelfHealingSystem

app = FastAPI(title="Engineer B API")

@app.get("/health")
def health():
    return {"status":"ok","service":"engineer_b_api"}

# --- DeepSeek proxy passthrough ---
class DSIn(BaseModel):
    prompt: str

@app.post("/proxy/deepseek")
def proxy_deepseek(body: DSIn):
    payload = json.dumps({"prompt": body.prompt}).encode("utf-8")
    req = urllib.request.Request(
        "http://deepseek_proxy:8010/llm/complete",
        data=payload,
        headers={"Content-Type":"application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

# --- Self-healing endpoints ---
class SnapshotIn(BaseModel):
    description: Optional[str] = "auto"

if not hasattr(app.state, "healer"):
    app.state.healer = SelfHealingSystem(db=None)

@app.post("/system/snapshot")
def create_snapshot(
    body: SnapshotIn = Body(default=SnapshotIn()),
    description: Optional[str] = Query(default=None)
):
    # Принимаем и body.description, и ?description=...
    desc = description or (body.description if body else None) or "auto"
    snap_id = app.state.healer.create_snapshot(desc)
    return {"status":"ok","snapshot_id": snap_id}

@app.post("/system/restore/{snap_id}")
def restore_snapshot(snap_id: int):
    app.state.healer.restore_from_snapshot(snap_id)
    return {"status":"ok","restored": snap_id}

# --- Tasks (stub) ---
_TASKS: List[Dict] = []

@app.get("/tasks")
def list_tasks(limit: int = 10):
    items = _TASKS[: max(0, limit)]
    return {"items": items, "count": len(items)}

@app.post("/tasks")
def create_task(payload: Dict):
    item = {"id": len(_TASKS) + 1, **payload}
    _TASKS.append(item)
    return {"ok": True, "task": item}
