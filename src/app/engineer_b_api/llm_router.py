# src/app/engineer_b_api/llm_router.py

from typing import Callable, Awaitable
import logging
import httpx
import os
import time
from datetime import datetime
from events import send_system_event

log = logging.getLogger(__name__)

# === 1. КЛАСС КУРАТОРА (GEMINI) ===
class GeminiCurator:
    def __init__(self, gemini_api_key, gemini_model_name):
        self.api_key = gemini_api_key
        self.model_name = gemini_model_name
        pass

    async def analyze_task(self, task: str) -> str:
        # Временная заглушка для CHECKLIST
        checklist = """
        - Проверить требования задачи на полноту.
        - Разбить задачу на шаги разработки: Код, Тест, Отчет.
        - Удостовериться, что Engineer использует инструменты (CodeInterpreter, submit_deployment_report).
        - Подтвердить готовность к развертыванию.
        """
        return checklist


# === 3. LLM ROUTER (МАРШРУТИЗАТОР) ===
class LLMRouter:
    def __init__(self, gemini_api_key, gemini_model_name):
        self.curator = GeminiCurator(gemini_api_key, gemini_model_name)
        log.info("Curator (Gemini) is initialized and active.")

    async def execute_task(self, task: str, executor: Callable[[str], Awaitable[str]]) -> str:
        """
        Основной цикл: Gemini (Curator) -> DeepSeek (Executor)
        """
        start_time = time.time()
        
        # Логирование запроса
        send_system_event(
            event_type="llm.request",
            payload={
                "task_preview": task[:200] if len(task) > 200 else task,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "cloud",
                "step": "curator_analysis"
            },
            source="llm_router"
        )

        # 1. Инспекция Куратором (Curator: Gemini)
        curator_checklist = await self.curator.analyze_task(task)

        # 2. Формирование финальной задачи для Исполнителя
        final_task_for_executor = f"""
        # CHECKLIST ОТ КУРАТОРА (GEMINI):
        {curator_checklist}

        --- ИСХОДНАЯ ЗАДАЧА ---
        {task}
        """

        # 3. Выполнение Исполнителем (Executor: DeepSeek)
        executor_response = await executor(final_task_for_executor)
        log.info(f"Executor (DeepSeek) Response Received")

        # 4. Формирование финального объединенного ответа
        final_combined_response = f"""
        === КУРАТОР (GEMINI) ===
        {curator_checklist}

        === ИНЖЕНЕР (DEEPSEEK) ===
        {executor_response}
        """
        
        # Логирование ответа и метрик
        elapsed_time = time.time() - start_time
        send_system_event(
            event_type="llm.response",
            payload={
                "response_preview": final_combined_response[:200] if len(final_combined_response) > 200 else final_combined_response,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "cloud",
                "elapsed_sec": round(elapsed_time, 2)
            },
            source="llm_router"
        )
        
        send_system_event(
            event_type="llm.inference.metrics",
            payload={
                "provider": "cloud",
                "model": "deepseek+gemini",
                "elapsed_sec": round(elapsed_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            },
            source="llm_router"
        )
        
        return final_combined_response
