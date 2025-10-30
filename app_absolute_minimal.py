from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "message": "MINIMAL WORKS"}

@app.get("/test")
def test():
    return {"message": "test endpoint works"}

if __name__ == "__main__":
    print("=== MINIMAL APP STARTING ===")
    uvicorn.run(app, host="0.0.0.0", port=8000)
