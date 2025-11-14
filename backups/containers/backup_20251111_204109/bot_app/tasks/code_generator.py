# tasks/code_generator.py
import aiohttp
import json
import logging
from config import DEEPSEEK_API_KEY, DEEPSEEK_PROXY_URL

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_PROXY_URL
    
    async def generate_code(self, task_description: str) -> str:
        """
        Генерирует код на основе описания задачи, 
        используя асинхронный клиент aiohttp.
        """
        
        # Инструкции для LLM: просим только чистый код
        prompt = f"""
        ТЗ: {task_description}
        
        Требования:
        1. Создай рабочий Python код.
        2. Код должен быть хорошо структурирован.
        3. Добавь документацию.
        4. Верни ТОЛЬКО код, обернутый в блок Markdown: ```python ... ```
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Используем формат Completion API, как в DeepSeekExecutor
        payload = {
            "prompt": prompt,
            "model": "deepseek-coder",
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        logger.info(f"API Call: {self.base_url}, Model: deepseek-coder")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload, headers=headers, timeout=120) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Извлекаем ответ LLM (логика может быть сложнее, но для начала достаточно)
                        llm_response = data.get('choices', [{}])[0].get('text', '')
                        
                        # Извлекаем только код из блока ```python
                        import re
                        match = re.search(r'```python\n(.*?)```', llm_response, re.DOTALL)
                        
                        if match:
                            return match.group(1).strip()
                        else:
                            # Если нет блока, возвращаем весь ответ
                            return llm_response.strip()
                    else:
                        error_text = await response.text()
                        logger.error(f"API Error: {response.status}, Details: {error_text}")
                        raise Exception(f"API Error: {response.status}")
                        
        except Exception as e:
            logger.exception("Error during code generation API call")
            raise Exception(f"Failed to connect or API error: {e}")