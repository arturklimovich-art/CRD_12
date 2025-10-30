from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Engineer_B_API_With_Jobs")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "with_jobs"}

# Try to import Jobs API
try:
    from jobs_ultra_simple import router as jobs_router
    app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])
    jobs_available = True
    print("✅ Jobs API integrated successfully")
except Exception as e:
    jobs_available = False
    print(f"❌ Jobs API integration failed: {e}")

# Smoke test
@app.get("/smoke/run")
async def smoke_test():
    return {
        "status": "smoke_test", 
        "message": "Smoke test working",
        "jobs_api": jobs_available
    }

# Debug routes
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
