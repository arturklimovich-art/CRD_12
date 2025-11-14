from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Engineer B API", version="4.1 - Self-Healing + Roadmap")

# Настройка шаблонов и статических файлов
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db_connection():
    """Подключение к базе данных"""
    return psycopg2.connect(os.getenv("DATABASE_URL", "postgres://crd_user:crd12@crd12_pgvector:5432/crd12"))

@app.get("/")
async def root():
    return {"message": "Engineer B API is running"}

@app.get("/roadmap")
async def get_roadmap_html(request: Request):
    """Главная страница Roadmap"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получить задачи из базы данных
        cur.execute("""
            SELECT id, title, status, progress_notes, created_at, updated_at 
            FROM eng_it.tasks 
            ORDER BY created_at DESC
        """)
        tasks = cur.fetchall()
        
        # Форматировать задачи
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                "id": task[0],
                "title": task[1],
                "status": task[2],
                "progress_notes": task[3],
                "created_at": task[4],
                "updated_at": task[5]
            })
        
        cur.close()
        conn.close()
        
        return templates.TemplateResponse("roadmap.html", {
            "request": request,
            "tasks": formatted_tasks,
            "total_tasks": len(formatted_tasks)
        })
        
    except Exception as e:
        logger.error(f"Error loading roadmap: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/api/roadmap")
async def get_roadmap_json():
    """API endpoint для Roadmap"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, title, status, progress_notes, created_at, updated_at 
            FROM eng_it.tasks 
            ORDER BY created_at DESC
        """)
        tasks = cur.fetchall()
        
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                "id": task[0],
                "title": task[1],
                "status": task[2],
                "progress_notes": task[3],
                "created_at": task[4].isoformat() if task[4] else None,
                "updated_at": task[5].isoformat() if task[5] else None
            })
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "tasks": formatted_tasks,
            "count": len(formatted_tasks)
        }
        
    except Exception as e:
        logger.error(f"Error in roadmap API: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Engineer B API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
