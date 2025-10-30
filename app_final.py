from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Engineer_B_API_Final")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "final_version"}

# Import Jobs API
jobs_available = False
try:
    from jobs_ultra_simple import router as jobs_router
    app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])
    jobs_available = True
    print("✅ Jobs API integrated successfully")
except Exception as e:
    print(f"❌ Jobs API integration failed: {e}")

# Import Smoke Test
smoke_available = False
try:
    from smoke_test import router as smoke_router
    app.include_router(smoke_router, tags=["smoke"])
    smoke_available = True
    print("✅ Smoke test integrated successfully")
except Exception as e:
    print(f"❌ Smoke test integration failed: {e}")

# Update health with status
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "Engineer_B_API",
        "jobs_api": jobs_available,
        "smoke_test": smoke_available
    }

# Debug endpoint
@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    return {"routes": routes}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
