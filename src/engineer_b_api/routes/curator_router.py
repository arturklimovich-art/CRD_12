"""
Curator API Router
Проверка кода перед применением патча
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

# Импортируем существующий Curator
import sys
sys.path.append('/app/curator')
from curator import Curator

router = APIRouter()
log = logging.getLogger(__name__)

class ReviewRequest(BaseModel):
    task_text: str
    code: str
    target_path: Optional[str] = None
    job_id: Optional[str] = None
    idempotency_key: Optional[str] = None

class ReviewResponse(BaseModel):
    decision: str  # "approve" or "reject"
    reasons: list
    score: int
    metrics: Dict[str, Any]

@router.post("/api/v1/validate", response_model=ReviewResponse)
async def validate_code(request: ReviewRequest):
    """
    Проверяет код через Curator
    
    Args:
        request: Запрос с кодом для проверки
    
    Returns:
        ReviewResponse: Результат проверки Curator
    """
    try:
        log.info(f"[CURATOR] Проверка кода для задачи: {request.task_text[:100]}...")
        
        # Создаём экземпляр Curator
        curator = Curator()
        
        # Проверяем код
        result = curator.review(
            task_text=request.task_text,
            code=request.code,
            target_path=request.target_path,
            job_id=request.job_id,
            idempotency_key=request.idempotency_key
        )
        
        log.info(f"[CURATOR] Результат: {result['decision']} (score: {result['score']})")
        
        if result['reasons']:
            log.warning(f"[CURATOR] Причины: {result['reasons']}")
        
        return ReviewResponse(**result)
        
    except Exception as e:
        log.error(f"[CURATOR] Ошибка проверки: {e}")
        raise HTTPException(status_code=500, detail=f"Curator error: {str(e)}")

@router.get("/api/v1/health")
def curator_health():
    """Проверка здоровья Curator"""
    return {"status": "healthy", "service": "Curator", "version": "1.0"}