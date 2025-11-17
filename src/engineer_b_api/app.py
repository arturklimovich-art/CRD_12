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
