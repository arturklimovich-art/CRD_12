from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Engineer B API Emergency", version="1.0")

@app.get("/roadmap")
async def get_roadmap():
    return {
        "status": "Roadmap Emergency Mode",
        "message": "System is in recovery mode. Full functionality will be restored soon.",
        "tasks": [
            {"id": "E1-B16", "title": "PatchService Integration", "status": "done"},
            {"id": "E1-B17", "title": "System Recovery", "status": "in_progress"}
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": "emergency"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
