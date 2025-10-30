from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Engineer_B_API")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "child_pid": 8}

# Jobs API Integration - Ultra Simple Version
from jobs_ultra_simple import router as jobs_router
app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
