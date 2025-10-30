import os, httpx, psycopg
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="DeepSeek Proxy")

class LLMRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.2

@app.get("/health")
def health():
    return {"status": "ok", "service": "deepseek_proxy"}

def _log_message(topic: str, role: str, content: str):
    # Неблокирующая попытка логирования; ошибки не роняют запрос
    try:
        # Подключение к БД через docker-сервис pgvector
        conn = psycopg.connect(
            host=os.getenv("PGHOST", "pgvector"),
            dbname=os.getenv("PGDATABASE", "crd12"),
            user=os.getenv("PGUSER", "crd_user"),
            password=os.getenv("PGPASSWORD", "crd12"),
            connect_timeout=3,
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages(topic, role, content) VALUES (%s,%s,%s)",
                    (topic, role, content[:8000]),
                )
        conn.close()
    except Exception as e:
        # лог в stdout, чтобы видеть причины в docker logs, но не падать
        print(f"[log_warn] messages insert failed: {e}", flush=True)

@app.post("/llm/complete")
async def complete(req: LLMRequest):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-coder")

    # логируем вход пользователя
    _log_message("deepseek", "user", req.prompt)

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": req.prompt}],
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{api_base}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    # логируем ответ ассистента
    _log_message("deepseek", "assistant", text)

    return {"ok": True, "text": text, "usage": usage}
