# src/app/engineer_b_api/llm_router.py

from typing import Callable, Awaitable
import logging
import httpx
import os

log = logging.getLogger(__name__)

# === 1. КЛАСС КУРАТОРА (GEMINI) ===
# Мы предполагаем, что этот класс был реализован ранее, но используем заглушку для CHECKLIST
# чтобы избежать ошибки вызова, пока не будет реализован полный код GeminiCurator
class GeminiCurator:
    # Здесь должна быть полная логика вызова Gemini API
    def __init__(self, gemini_api_key, gemini_model_name):
        # ... (инициализация клиента)
        pass
        
    async def analyze_task(self, task: str) -> str:
        # Временная заглушка для CHECKLIST, пока не настроен Gemini API:
        checklist = """
        - Проверить требования задачи на полноту.
        - Разбить задачу на шаги разработки: Код, Тест, Отчет.
        - Удостовериться, что Engineer использует инструменты (CodeInterpreter, submit_deployment_report).
        - Подтвердить готовность к развертыванию.
        """
        return checklist


# === 3. LLM ROUTER (МАРШРУТИЗАТОР) ===
class LLMRouter:
    # Конструктор принимает только ключи, а не 'tools'
    def __init__(self, gemini_api_key, gemini_model_name): 
        # ВОССТАНОВЛЕНИЕ: Включаем Куратора (Gemini)
        self.curator = GeminiCurator(gemini_api_key, gemini_model_name)
        log.info("Curator (Gemini) is initialized and active.")

    async def execute_task(self, task: str, executor: Callable[[str], Awaitable[str]]) -> str:
        """
        Основной цикл: Gemini (Curator) -> DeepSeek (Executor)
        """
        
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
        return final_combined_response