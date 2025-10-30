# src/app/deepseek_proxy/app.py (ФИНАЛЬНАЯ ЛОГИКА ДЛЯ DEEPSEEK)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
import logging
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - DeepSeekProxy - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Константы API DeepSeek ---
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")

# --- Схемы данных ---
class CompletionRequest(BaseModel):
    # Engineer B отправляет нам просто 'prompt'
    prompt: str

app = FastAPI(title="DeepSeek Proxy", version="1.0")

# --- Главный эндпоинт для Engineer B ---
@app.post("/llm/complete")
async def complete_llm_request(request: CompletionRequest) -> Dict[str, Any]:
    if not DEEPSEEK_API_KEY:
        log.error("❌ DEEPSEEK_API_KEY not set.")
        # Возвращаем понятную заглушку, если ключа нет
        return {"ok": True, "output": "DeepSeek Proxy: API Key Missing (Please check .env)"}

    # 1. Формирование запроса для DeepSeek API (стандартный формат Chat Completion)
    deepseek_payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "user", "content": request.prompt} # Наш промпт - это content
        ],
        "stream": False,
        "max_tokens": 2048
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    log.info(f"➡️ Forwarding request to DeepSeek API ({DEEPSEEK_MODEL})...")
    
    # 2. Асинхронный HTTP-запрос
    try:
        # Устанавливаем таймаут 120 секунд для больших запросов LLM
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                json=deepseek_payload,
                headers=headers
            )
            response.raise_for_status() # Вызовет исключение при 4xx/5xx ошибке
            
            deepseek_data = response.json()
            
            # 3. Извлечение ответа и форматирование для Engineer B
            # DeepSeek возвращает ответ в choices[0].message.content
            content = deepseek_data.get('choices', [{}])[0].get('message', {}).get('content')
            
            if content:
                log.info("✅ DeepSeek response received and parsed successfully.")
                return {"ok": True, "output": content}
            else:
                log.error(f"❌ DeepSeek returned empty content. Full response: {deepseek_data}")
                return {"ok": False, "output": f"DeepSeek Proxy Error: Empty content in response. Details: {deepseek_data}"}

    except httpx.HTTPStatusError as e:
        log.error(f"❌ DeepSeek API returned HTTP error: {e.response.status_code}. Response: {e.response.text}")
        return {"ok": False, "output": f"DeepSeek API HTTP Error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        log.error(f"❌ Proxy forwarding failed: {e}")
        return {"ok": False, "output": f"DeepSeek Proxy Connection Error: {str(e)}"}


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "healthy", "service": "DeepSeek Proxy", "model": DEEPSEEK_MODEL}