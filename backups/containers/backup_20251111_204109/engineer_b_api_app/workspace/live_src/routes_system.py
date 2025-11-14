from fastapi import APIRouter
from agents.self_healing import SelfHealingSystem

router = APIRouter()

# Для простоты используем без подключения к БД
healer = SelfHealingSystem(db=None)

@router.post("/system/snapshot")
async def create_snapshot(description: str = "auto"):
    snap_id = healer.create_snapshot(description)
    return {"status": "ok", "snapshot_id": snap_id}

@router.post("/system/restore/{snap_id}")
async def restore_snapshot(snap_id: int):
    healer.restore_from_snapshot(snap_id)
    return {"status": "ok", "restored": snap_id}
