from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
import os
import logging
import httpx

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
    """Navigator HTML Dashboard - показывает текущую задачу и её шаги"""
    try:
        # Получаем текущую задачу
        async with httpx.AsyncClient() as client:
            current_resp = await client.get("http://localhost:8000/api/current")
            current_data = current_resp.json()
            
            current_task = current_data.get("task")
            if not current_task:
                return templates.TemplateResponse("navigator.html", {
                    "request": request,
                    "error": "No current task found",
                    "current_task": None,
                    "steps": [],
                    "stats": {}
                })
            
            # Получаем шаги текущей задачи
            task_id = current_task['id']
            steps_resp = await client.get(f"http://localhost:8000/api/navigator/steps/{task_id}")
            steps_data = steps_resp.json()
            
            steps = steps_data.get("steps", [])
            steps_count = steps_data.get("steps_count", 0)
            
            # Подсчёт статистики шагов
            stats = {
                "total": steps_count,
                "done": sum(1 for s in steps if s.get('done') or s.get('status') == 'done'),
                "in_progress": sum(1 for s in steps if s.get('status') == 'in_progress'),
                "planned": sum(1 for s in steps if s.get('status') == 'planned'),
            }
            stats["completion"] = round((stats["done"] / stats["total"] * 100) if stats["total"] > 0 else 0, 1)
            
            return templates.TemplateResponse("navigator.html", {
                "request": request,
                "current_task": current_task,
                "steps": steps,
                "stats": stats
            })
            
    except Exception as e:
        logger.error(f"Error loading navigator: {e}")
        return templates.TemplateResponse("navigator.html", {
            "request": request,
            "error": str(e),
            "current_task": None,
            "steps": [],
            "stats": {}
        })