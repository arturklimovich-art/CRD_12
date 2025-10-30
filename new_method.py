import os
import httpx

async def analyze_with_deepseek(self, task: str) -> str:
    """Анализ задачи с помощью реального DeepSeek API"""
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_url = "https://api.deepseek.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-coder",
            "messages": [
                {"role": "user", "content": f"Проанализируй задачу: {task}"}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return "Ошибка: неверный формат ответа от AI"
            else:
                return f"Ошибка API: {response.status_code} - {response.text}"
                
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        return f"Ошибка связи с AI: {str(e)}"
