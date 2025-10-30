from fastapi import APIRouter

router = APIRouter()

@router.get("/ready")
async def ready_check():
    return {"status": "ready"}
