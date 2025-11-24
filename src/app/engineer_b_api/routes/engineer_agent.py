"""
Engineer B Agent API
Endpoint для генерации кода на основе задач
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx
import os
import logging
import json

router = APIRouter()
log = logging.getLogger(__name__)

# Конфигурация LLM
DEEPSEEK_PROXY_URL = os.getenv("DEEPSEEK_PROXY_URL", "http://deepseek_proxy:8010/llm/complete")

class AnalyzeRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None

class AnalyzeResponse(BaseModel):
    engineer_status: str  # "passed" or "failed"
    generated_code: Optional[str] = None
    report: Dict[str, Any]
    error: Optional[str] = None

@router.post("/agent/analyze", response_model=AnalyzeResponse)
async def analyze_task(request: AnalyzeRequest):
    """
    Анализирует задачу и генерирует код
    
    Args:
        request: Запрос с описанием задачи и контекстом
    
    Returns:
        AnalyzeResponse: Результат генерации кода
    """
    try:
        log.info(f"[ENGINEER_AGENT] Получена задача: {request.task[:100]}...")
        
        # Формируем prompt для LLM
        prompt = f"""You are Engineer B - a professional Python code generator.

TASK:
{request.task}

INSTRUCTIONS:
1. Analyze the task carefully
2. Generate ONLY the code that needs to be changed/added
3. Use proper Python syntax
4. Include comments in Russian
5. Return code in a clear, executable format
6. Do NOT include explanations outside code blocks

Generate the complete, working code now:
"""
        
        # Добавляем контекст если есть
        if request.context:
            prompt += f"\n\nSYSTEM CONTEXT:\n{json.dumps(request.context, indent=2, ensure_ascii=False)}\n"
        
        # Вызываем DeepSeek Proxy
        log.info(f"[ENGINEER_AGENT] Отправка запроса в DeepSeek Proxy: {DEEPSEEK_PROXY_URL}")
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            llm_response = await client.post(
                DEEPSEEK_PROXY_URL,
                json={"prompt": prompt}
            )
        
        if llm_response.status_code != 200:
            log.error(f"[ENGINEER_AGENT] DeepSeek Proxy error: {llm_response.status_code} - {llm_response.text}")
            return AnalyzeResponse(
                engineer_status="failed",
                generated_code=None,
                report={"description": f"DeepSeek Proxy error: {llm_response.status_code}"},
                error=f"Proxy returned status {llm_response.status_code}"
            )
        
        llm_data = llm_response.json()
        
        # Парсим ответ DeepSeek Proxy
        if not llm_data.get("ok", False):
            log.error(f"[ENGINEER_AGENT] DeepSeek Proxy returned ok=false: {llm_data.get('output', 'No output')}")
            return AnalyzeResponse(
                engineer_status="failed",
                generated_code=None,
                report={"description": "DeepSeek Proxy returned error"},
                error=llm_data.get("output", "Unknown error")
            )
        
        generated_code = llm_data.get("output", "")
        
        if not generated_code or len(generated_code.strip()) < 10:
            log.warning("[ENGINEER_AGENT] DeepSeek вернул пустой или слишком короткий код")
            return AnalyzeResponse(
                engineer_status="failed",
                generated_code=None,
                report={"description": "Generated code is empty or too short"},
                error="Code generation failed - empty output"
            )
        
        log.info(f"[ENGINEER_AGENT] ✅ Код сгенерирован успешно ({len(generated_code)} символов)")
        
        return AnalyzeResponse(
            engineer_status="passed",
            generated_code=generated_code,
            report={
                "description": "Code generated successfully by Engineer B via DeepSeek",
                "code_length": len(generated_code),
                "llm_model": "deepseek-chat"
            },
            error=None
        )
        
    except httpx.TimeoutException:
        log.error("[ENGINEER_AGENT] Timeout при обращении к DeepSeek Proxy")
        return AnalyzeResponse(
            engineer_status="failed",
            generated_code=None,
            report={"description": "DeepSeek Proxy timeout"},
            error="Timeout waiting for LLM response (180s)"
        )
    except Exception as e:
        log.error(f"[ENGINEER_AGENT] Ошибка: {e}")
        return AnalyzeResponse(
            engineer_status="failed",
            generated_code=None,
            report={"description": f"Internal error: {str(e)}"},
            error=str(e)
        )