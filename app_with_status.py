from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Engineer_B_API")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Engineer_B_API"}

# Import Jobs API
try:
    from jobs_ultra_simple import router as jobs_router
    app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])
    jobs_available = True
    print("✅ Jobs API integrated successfully")
except Exception as e:
    jobs_available = False
    print(f"❌ Jobs API integration failed: {e}")

# Import Smoke Test
try:
    from smoke_test import router as smoke_router
    app.include_router(smoke_router, tags=["smoke"])
    smoke_available = True
    print("✅ Smoke test integrated successfully")
except Exception as e:
    smoke_available = False
    print(f"❌ Smoke test integration failed: {e}")

# Import System Status
try:
    from system_status import router as status_router
    app.include_router(status_router, prefix="/system", tags=["system"])
    status_available = True
    print("✅ System status integrated successfully")
except Exception as e:
    status_available = False
    print(f"❌ System status integration failed: {e}")

# Update health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "Engineer_B_API",
        "jobs_api": jobs_available,
        "smoke_test": smoke_available,
        "system_status": status_available
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
