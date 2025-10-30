from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="Engineer_B_API_Port8030")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "port": 8030}

# Import Jobs API
try:
    from jobs_ultra_simple import router as jobs_router
    app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])
    jobs_available = True
    print("✅ Jobs API integrated on port 8030")
except Exception as e:
    jobs_available = False
    print(f"❌ Jobs API failed: {e}")

# Import Smoke Test
try:
    from smoke_test import router as smoke_router
    app.include_router(smoke_router, tags=["smoke"])
    smoke_available = True
    print("✅ Smoke test integrated on port 8030")
except Exception as e:
    smoke_available = False
    print(f"❌ Smoke test failed: {e}")

# Update health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "port": 8030,
        "jobs_api": jobs_available,
        "smoke_test": smoke_available
    }

# Test endpoint
@app.get("/test")
async def test_endpoint():
    return {"message": "Direct port 8030 test"}

if __name__ == "__main__":
    print("=== STARTING UVICORN ON PORT 8030 ===")
    uvicorn.run(app, host="0.0.0.0", port=8030)
