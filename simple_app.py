from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Engineer B API - Simple Working Version"}

@app.get("/roadmap")
async def roadmap():
    return {"status": "Roadmap is working", "version": "simple"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting Engineer B API...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
