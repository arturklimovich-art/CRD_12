from fastapi import FastAPI, Request
from routes import curator_router
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
import os
import logging
import httpx
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Engineer B API", version="4.1 - Self-Healing + Roadmap")

# Roadmap API router
from routes.roadmap_api import router as roadmap_api_router
from routes.engineer_agent import router as engineer_agent_router
app.include_router(roadmap_api_router)
app.include_router(engineer_agent_router)

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


# Health check endpoint for Docker
    return {status: ok}

# Health check endpoint for Docker

@app.get("/health")

# Health check endpoint for Docker

@app.get("/health")
async def health():
    return {"status": "ok"}

# System Context API для агентов (Bot, Engineer_B, Curator)

@app.get("/api/system/context")
async def get_system_context():
    """
    Возвращает контекст системы для агентов.
    Используется Bot, Engineer_B и Curator для понимания архитектуры.
    """
    return {
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "host": "pgvector",
            "port": 5432,
            "name": "crd12",
            "user": "crd_user",
            "schemas": ["eng_it", "core"],
            "tables": {
                "eng_it.roadmap_tasks": {
                    "description": "Основные задачи Roadmap (25 задач)",
                    "columns": ["id", "code", "title", "description", "status", "priority", "assigned_to", "labels", "created_at", "updated_at", "completed_at"],
                    "statuses": ["planned", "in_progress", "done", "cancelled"],
                    "primary_key": "id",
                    "unique_key": "code"
                },
                "eng_it.progress_navigator": {
                    "description": "Детальные шаги выполнения задач (74 шага)",
                    "columns": ["id", "task_code", "title", "description", "level", "module", "priority", "status", "estimated_hours", "actual_hours", "created_at", "updated_at"],
                    "statuses": ["passed", "failed", "in_progress"],
                    "levels": ["B", "S", "L"]
                },
                "core.events": {
                    "description": "Логирование всех событий системы",
                    "columns": ["id", "event_type", "entity_type", "entity_id", "data", "created_at"],
                    "event_types": ["task_started", "task_completed", "tz_generated", "status_updated", "code_generated", "curator_approved"]
                },
                "eng_it.tasks": {
                    "description": "Связь с roadmap_tasks и дополнительные атрибуты",
                    "columns": ["id", "roadmap_task_id", "title", "description", "status", "created_at", "updated_at"]
                }
            }
        },
        "api": {
            "base_url": "http://engineer_b_api:8000",
            "external_url": "http://localhost:8001",
            "endpoints": {
                "roadmap": {
                    "GET /api/roadmap": "Получить все задачи Roadmap",
                    "GET /api/current": "Получить текущую задачу (in_progress с min priority)",
                    "GET /api/roadmap/{task_id}": "Получить задачу по ID"
                },
                "navigator": {
                    "GET /api/navigator/steps/{task_id}": "Получить шаги конкретной задачи",
                    "GET /api/navigator/all": "Получить все 74 шага Navigator"
                },
                "system": {
                    "GET /health": "Health check",
                    "GET /api/system/context": "Этот endpoint - контекст системы"
                }
            }
        },
        "files": {
            "bot": {
                "main": "/app/bot.py",
                "commands": "/app/commands/",
                "tasks": "/app/tasks/task_manager.py"
            },
            "api": {
                "main": "/app/app.py",
                "templates": "/app/templates/navigator.html",
                "static": "/app/static/"
            },
            "docs": {
                "roadmap": "/app/docs/ROADMAP.yaml",
                "passport": "/app/docs/SYSTEM_PASSPORT.md"
            }
        },
        "containers": {
            "bot": {
                "name": "crd12_bot",
                "image": "python:3.11-slim",
                "mode": "polling"
            },
            "api": {
                "name": "crd12_engineer_b_api",
                "image": "python:3.11-slim",
                "ports": ["8001:8000", "8031:8030"]
            },
            "db": {
                "name": "crd12_pgvector",
                "image": "pgvector/pgvector:pg16",
                "port": "5432:5432"
            }
        },
        "workflow": {
            "self_building": {
                "description": "Автоматический путь выполнения задач",
                "steps": [
                    "1. get_next_self_building_task() из progress_navigator",
                    "2. Bot (ChatGPT) генерирует ТЗ",
                    "3. Engineer_B генерирует код",
                    "4. Curator (Gemini) проверяет и одобряет",
                    "5. Patch применяется",
                    "6. Статус → done"
                ]
            },
            "manual": {
                "description": "Ручной путь с проверками",
                "steps": [
                    "1. Человек берет задачу из roadmap",
                    "2. Человек пишет patch",
                    "3. Patch проходит те же проверки",
                    "4. Curator одобряет",
                    "5. Статус → done"
                ]
            }
        },
        "env_variables": {
            "DATABASE_URL": "postgresql://crd_user:crd_password@pgvector:5432/crd12",
            "ENGINEER_B_API_URL": "http://engineer_b_api:8000",
            "CURATOR_API_URL": "http://curator:8080 (или заглушка)",
            "TELEGRAM_BOT_TOKEN": "set in .env",
            "OPENAI_API_KEY": "set in .env"
        }
    }
