from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Engineer B API", version="4.1 - Self-Healing + Roadmap")

# Roadmap API router
from routes.roadmap_api import router as roadmap_api_router
app.include_router(roadmap_api_router)

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
        
        cur.execute("""
            SELECT id, code, title, status, description, priority, steps, created_at, updated_at, completed_at
            FROM eng_it.roadmap_tasks
            ORDER BY priority DESC, code
        """)
        
        tasks = cur.fetchall()
        cur.close()
        conn.close()
        
        return templates.TemplateResponse("roadmap.html", {
            "request": request,
            "tasks": tasks
        })
    except Exception as e:
        logger.error(f"Error loading roadmap: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/navigator", response_class=HTMLResponse)
async def navigator_page(request: Request):
    """Navigator HTML Dashboard - показывает Roadmap визуально"""
    try:
        # Получаем данные из API
        import httpx
        async with httpx.AsyncClient() as client:
            roadmap_resp = await client.get("http://localhost:8000/api/roadmap")
            roadmap_data = roadmap_resp.json()
            
            truth_resp = await client.get("http://localhost:8000/api/truth/matrix")
            truth_data = truth_resp.json()
        
        # Подготовка данных для шаблона
        tasks = roadmap_data.get("tasks", [])
        total_tasks = roadmap_data.get("total_tasks", 0)
        
        # Статистика по статусам
        stats = {"done": 0, "in_progress": 0, "planned": 0}
        for task in tasks:
            status = task.get("status", "unknown")
            if status in stats:
                stats[status] += 1
        
        return templates.TemplateResponse("navigator.html", {
            "request": request,
            "tasks": tasks,
            "total_tasks": total_tasks,
            "stats": stats,
            "truth_status": truth_data.get("status", "unknown"),
            "truth_timestamp": truth_data.get("timestamp", "N/A")
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>", status_code=500)