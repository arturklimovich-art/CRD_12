from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import os
import sys

# Jobs API Integration - Ultra Simple Version
try:
    from jobs_ultra_simple import router as jobs_router
    jobs_available = True
except ImportError as e:
    print(f"Jobs API not available: {e}")
    jobs_available = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Engineer_B_API starting...")
    if jobs_available:
        print("Jobs API integrated successfully")
    yield
    # Shutdown
    print("Engineer_B_API shutting down...")

app = FastAPI(title="Engineer_B_API", lifespan=lifespan)

# Import existing routes
from routes_system import router as system_router
from apply_patch_simple import router as patch_router
from ready_check import router as ready_router

app.include_router(system_router)
app.include_router(patch_router, prefix="/agent", tags=["agent"])
app.include_router(ready_router)

# Include Jobs API if available
if jobs_available:
    app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "child_pid": os.getpid(), "jobs_api": jobs_available}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
