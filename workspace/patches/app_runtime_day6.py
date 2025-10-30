from fastapi import FastAPI
from pydantic import BaseModel
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
    description: str = "auto"

# Инициализируем healer один раз
if not hasattr(app.state, "healer"):
    app.state.healer = SelfHealingSystem(db=None)

@app.post("/system/snapshot")
def create_snapshot(body: SnapshotIn):
    snap_id = app.state.healer.create_snapshot(body.description)
    return {"status":"ok","snapshot_id": snap_id}

@app.post("/system/restore/{snap_id}")
def restore_snapshot(snap_id: int):
    app.state.healer.restore_from_snapshot(snap_id)
    return {"status":"ok","restored": snap_id}
