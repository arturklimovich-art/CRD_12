#!/usr/bin/env python3
"""
Intelligent Agent with FastAPI Integration
Combines AI agent functionality with FastAPI web server
"""

import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
import sys

# ===== FASTAPI SETUP =====

# Jobs API Integration
try:
    from jobs_ultra_simple import router as jobs_router
    jobs_available = True
except ImportError as e:
    print(f"Jobs API not available: {e}")
    jobs_available = False

# Smoke Test Integration  
try:
    from smoke_test import router as smoke_router
    smoke_available = True
except ImportError as e:
    print(f"Smoke test not available: {e}")
    smoke_available = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Intelligent Agent with FastAPI starting...")
    if jobs_available:
        print("Jobs API integrated successfully")
    if smoke_available:
        print("Smoke test integrated successfully")
    yield
    # Shutdown
    print("Intelligent Agent shutting down...")

app = FastAPI(title="Intelligent_Agent_API", lifespan=lifespan)

# Import existing routes
try:
    from routes_system import router as system_router
    app.include_router(system_router)
except ImportError as e:
    print(f"System routes not available: {e}")

try:
    from apply_patch_simple import router as patch_router
    app.include_router(patch_router, prefix="/agent", tags=["agent"])
except ImportError as e:
    print(f"Patch routes not available: {e}")

try:
    from ready_check import router as ready_router
    app.include_router(ready_router)
except ImportError as e:
    print(f"Ready check not available: {e}")

# Include Jobs API if available
if jobs_available:
    app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])

# Include Smoke Test if available
if smoke_available:
    app.include_router(smoke_router, tags=["smoke"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "Intelligent_Agent_API",
        "jobs_api": jobs_available,
        "smoke_test": smoke_available
    }

# Diagnostic endpoint
@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": getattr(route, "path", "N/A"),
            "name": getattr(route, "name", "N/A"), 
            "methods": getattr(route, "methods", [])
        })
    return {"routes": routes}

# ===== INTELLIGENT AGENT FUNCTIONALITY =====
# (Existing intelligent agent code would go here)

def start_fastapi():
    """Start the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)

if __name__ == "__main__":
    start_fastapi()
