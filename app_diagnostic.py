from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Engineer_B_API_Diagnostic")

print("=== STARTING DIAGNOSTIC APP ===")

# Import Jobs API
print("1. Attempting to import Jobs API...")
try:
    from jobs_ultra_simple import router as jobs_router
    print("   ✅ Jobs router imported")
    print(f"   Jobs router routes: {[route.path for route in jobs_router.routes]}")
    
    app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])
    print("   ✅ Jobs router included with prefix /api/v1")
    jobs_available = True
except Exception as e:
    print(f"   ❌ Jobs API failed: {e}")
    jobs_available = False

# Import Smoke Test
print("2. Attempting to import Smoke Test...")
try:
    from smoke_test import router as smoke_router
    print("   ✅ Smoke router imported")
    print(f"   Smoke router routes: {[route.path for route in smoke_router.routes]}")
    
    app.include_router(smoke_router, tags=["smoke"])
    print("   ✅ Smoke router included")
    smoke_available = True
except Exception as e:
    print(f"   ❌ Smoke test failed: {e}")
    smoke_available = False

print("3. Setting up basic routes...")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "diagnostic",
        "jobs_api": jobs_available,
        "smoke_test": smoke_available
    }

@app.get("/simple_test")
async def simple_test():
    return {"message": "Simple test works"}

@app.get("/debug/all_routes")
async def debug_all_routes():
    """Show all routes with full details"""
    routes_info = []
    for route in app.routes:
        route_info = {
            "path": getattr(route, "path", "N/A"),
            "name": getattr(route, "name", "N/A"),
            "methods": list(getattr(route, "methods", [])),
            "endpoint": str(getattr(route, "endpoint", "N/A"))
        }
        routes_info.append(route_info)
    
    return {
        "total_routes": len(routes_info),
        "routes": routes_info
    }

print("4. Application setup complete")
print(f"   Total routes: {len(app.routes)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
