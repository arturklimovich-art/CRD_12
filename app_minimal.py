from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Engineer_B_API_Minimal")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "minimal"}

# Minimal smoke test endpoint
@app.get("/smoke/run")
async def smoke_test():
    return {"status": "smoke_test", "message": "Smoke test working"}

# Minimal jobs test endpoint  
@app.get("/api/v1/jobs/test")
async def jobs_test():
    return {"message": "Jobs API test working", "status": "success"}

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
