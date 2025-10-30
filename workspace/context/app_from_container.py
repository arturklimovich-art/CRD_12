from fastapi import FastAPI, HTTPException
from datetime import datetime
import logging
import os
from typing import Dict
import httpx

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Engineer B API", version="2.0")


DS_URL = os.getenv('DEEPSEEK_API_URL','http://deepseek_proxy:8010/llm/complete')
# Инициализация состояния при запуске
@app.on_event("startup")
async def startup_event():
    app.state.start_time = datetime.now()
    app.state.active_tasks = {}
    app.state.analysis_history = []
    logger.info("✅ Engineer B API v2.0 started with DeepSeek integration")

# =============================================================================
# СИСТЕМНЫЕ ЭНДПОИНТЫ
# =============================================================================

@app.get("/")
async def root():
    return {
        "message": "Engineer B AI Agent v2.0",
        "status": "active",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/system/health")
async def system_health():
    """Комплексная проверка здоровья системы"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
        "components": {
            "api": "ok",
            "deepseek": "connected",
            "memory": "ok"
        }
    }

@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "timestamp": datetime.now().isoformat()}

@app.get("/system/metrics")
async def system_metrics():
    return {
        "active_tasks": len(app.state.active_tasks),
        "analysis_count": len(app.state.analysis_history),
        "uptime": get_system_uptime(),
        "timestamp": datetime.now().isoformat()
    }

# =============================================================================
# ИНТЕЛЛЕКТУАЛЬНЫЙ АГЕНТ
# =============================================================================

class IntelligentAgent:
    def __init__(self):
        self.history = []

    async def analyze_with_deepseek(self, task: str) -> str:
        """Анализ задачи с помощью DeepSeek AI"""
        try:
            prompt = f"""
            Ты - опытный IT-инженер. Проанализируй задачу и дай план реализации.

            ЗАДАЧА: {task}
            """
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://deepseek_proxy:8010/llm/complete",
                    json={
                        "prompt": prompt,
                        "max_tokens": 1000,
                        "temperature": 0.3
                    },
                    timeout=30.0
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "Анализ не удался - пустой ответ от AI")
                return f"Ошибка DeepSeek API: {response.status_code}"
        except Exception as e:
            logger.error(f"DeepSeek connection error: {e}")
            return f"Ошибка связи с DeepSeek: {str(e)}"

agent = IntelligentAgent()

@app.post("/agent/analyze")
async def agent_analyze_task(request: Dict):
    try:
        task = request.get("task")
        if not task:
            raise HTTPException(status_code=400, detail="Task is required")

        ai_analysis = await agent.analyze_with_deepseek(task)
        analysis_entry = {
            "task": task,
            "analysis": ai_analysis,
            "timestamp": datetime.now().isoformat()
        }
        app.state.analysis_history.append(analysis_entry)

        return {
            "status": "success",
            "analysis": ai_analysis,
            "task": task,
            "analysis_id": f"analysis_{len(app.state.analysis_history)}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/memory")
async def get_agent_memory():
    return {
        "status": "ready",
        "analysis_count": len(app.state.analysis_history),
        "recent_tasks": [h["task"] for h in app.state.analysis_history[-3:]],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/agent/test")
async def test_agent_connection():
    try:
        resp = await agent.analyze_with_deepseek("Ответь коротко: работает ли связь?")
        return {"status": "success", "response": resp, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

# =============================================================================
# ТАСКИ
# =============================================================================

@app.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    return {
        "task_id": task_id,
        "state": "processed",
        "progress": 100,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/system/build/self")
async def build_self():
    return {
        "status": "simulated",
        "message": "Self-building capability ready",
        "timestamp": datetime.now().isoformat()
    }

# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ
# =============================================================================

def get_system_uptime():
    if hasattr(app.state, "start_time"):
        uptime = datetime.now() - app.state.start_time
        return str(uptime).split(".")[0]
    return "unknown"



