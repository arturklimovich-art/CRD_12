#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime

# Импорты для Patch API
from patch_manager import PatchManager

# ✅ НОВОЕ: Импорт Roadmap Router
from routes.roadmap import router as roadmap_router

app = FastAPI(
    title="Engineer B API + Roadmap Module",
    version="2.1",
    description="Engineer B API with integrated Roadmap Truth System"
)

# ✅ НОВОЕ: Подключение Roadmap Router
app.include_router(roadmap_router)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "ts": datetime.utcnow().isoformat() + "Z",
        "version": "2.1",
        "modules": ["engineer_b", "patch_manager", "roadmap"]
    }

@app.get("/")
async def root():
    return {
        "message": "Engineer B API + Roadmap Module",
        "version": "2.1",
        "docs": "/docs",
        "roadmap_api": "/api/v1/roadmap",
        "health": "/health"
    }

# Patch API endpoints (существующие)
pm = PatchManager(
    db_dsn=os.getenv("DATABASE_URL", "postgres://crd_user:crd12@crd12_pgvector:5432/crd12")
)

@app.post("/api/patches/{patch_id}/apply")
async def apply_patch(patch_id: str, request: Request):
    """Применить патч (существующий endpoint)"""
    approve_token = await request.body()
    approve_token_str = approve_token.decode('utf-8').strip()
    
    try:
        success, message = pm.apply_patch(patch_id, approve_token_str)
        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": message,
                    "patch_id": patch_id
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": message}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
