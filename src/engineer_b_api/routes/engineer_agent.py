import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from intelligent_agent import IntelligentAgent
from intelligent_agent import DeepSeekExecutor

log = logging.getLogger(__name__)
router = APIRouter()

DEEPSEEK_PROXY_URL = "http://deepseek_proxy:8010/llm/complete"

class AnalyzeRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None

class AnalyzeResponse(BaseModel):
    engineer_status: str
    generated_code: str
    report: Dict[str, Any] = {}

@router.post("/agent/analyze", response_model=AnalyzeResponse)
async def analyze_task(request: AnalyzeRequest):
    """
    Анализирует задачу и генерирует код используя IntelligentAgent
    
    Args:
        request: Запрос с описанием задачи и контекстом
    
    Returns:
        AnalyzeResponse: Результат генерации кода с target_path_hint
    """
    try:
        log.info(f"[ENGINEER_AGENT] Получена задача: {request.task[:100]}...")
        log.info(f"[ENGINEER_AGENT] Используем IntelligentAgent для обработки")
        
        # Use IntelligentAgent for proper task processing
        # Create DeepSeekExecutor
        executor = DeepSeekExecutor("http://deepseek_proxy:8010/llm/complete")
        agent = IntelligentAgent(deepseek_executor=executor)
        result = await agent.run_cycle(task_text=request.task)
        # DEBUG: Показать что вернул IntelligentAgent
        log.info(f"[ENGINEER_AGENT] [DEBUG] result keys = {list(result.keys())}")
        log.info(f"[ENGINEER_AGENT] [DEBUG] status = {result.get('status', 'N/A')}")
        log.info(f"[ENGINEER_AGENT] [DEBUG] code length = {len(result.get('code', ''))}")
        if "error" in result:
            log.error(f"[ENGINEER_AGENT] [DEBUG] ERROR TEXT = {result.get('error', 'N/A')}")
        
        # Extract status, code, and report
        status = result.get("status", "failed")
        code = result.get("code", "")
        report = result.get("report", {})
        
        # Log target_path_hint if present
        if "target_path_hint" in report:
            log.info(f"[ENGINEER_AGENT] [DEBUG] FULL REPORT = {report}")
            log.info(f"[ENGINEER_AGENT] Извлечён target_path: {report['target_path_hint']}")
        else:
            log.warning(f"[ENGINEER_AGENT] target_path_hint не найден в задаче")
        
        engineer_status = "passed" if status == "ok" and code else "failed"
        
        log.info(f"[ENGINEER_AGENT] ✅ Код сгенерирован успешно ({len(code)} символов)")
        
        return AnalyzeResponse(
            engineer_status=engineer_status,
            generated_code=code,
            report=report
        )
        
    except Exception as e:
        log.error(f"[ENGINEER_AGENT] ❌ Ошибка: {str(e)}")
        import traceback
        log.error(traceback.format_exc())
        return AnalyzeResponse(
            engineer_status="failed",
            generated_code="",
            report={"error": str(e)}
        )
