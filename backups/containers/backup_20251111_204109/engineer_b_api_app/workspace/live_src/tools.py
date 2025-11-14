# tools.py
import json
import os
import sys
import io
import tempfile
import runpy
import re
from typing import Dict, Any, Tuple

# ====================================================================
# 1. ФУНКЦИИ ДЛЯ ОТЧЕТНОСТИ (Function Calling)
# ====================================================================

def submit_deployment_report(
    patch_description: str, 
    files_modified: str, 
    tests_status: str, 
    smoke_test_result: str,
    deployment_ready: bool = False
) -> Dict:
    """
    Создает структурированный отчет о готовности к развертыванию, который бот 
    интерпретирует как запрос на подтверждение (deployment_request).
    """
    
    ready_status = deployment_ready 

    return {
        "action": "deployment_request",
        "description": patch_description,
        "files_modified": [files_modified], # Всегда список
        "tests_status": tests_status,
        "smoke_test_result": smoke_test_result,
        "deployment_ready": ready_status
    }

def submit_pull_request(files_to_commit: str, pr_title: str) -> str:
    """
    Инструмент для создания Pull Request в GitHub.
    Возвращает строку с подтверждением создания PR.
    """
    return f"Успех: Pull Request {pr_title} для файлов {files_to_commit} успешно создан. Ожидает..."


# ====================================================================
# 2. ИНТЕРПРЕТАТОР КОДА (CodeInterpreter)
# ====================================================================

class CodeInterpreter:
    """
    Класс для безопасного исполнения кода, сгенерированного LLM.
    Методы из предыдущей версии удалены/обновлены.
    """

    @staticmethod
    def run_smoke_test(code_content: str, entry_point: str = "main", *args, **kwargs) -> Tuple[bool, str]:
        """
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Реализация статического метода run_smoke_test.
        Исполняет предоставленный Python-код во временном файле.
        Ожидает, что код содержит функцию с именем 'entry_point' (по умолчанию 'main').
        Возвращает (успех: bool, лог: str).
        """
        success = False
        log_output = ""
        tmp_path = None
        
        # Перенаправляем stdout для захвата вывода кода
        original_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        # Оборачиваем код в функцию, если это необходимо
        # Наш LLM должен генерировать функцию. Мы ищем ее и вызываем.
        code_blocks = re.findall(r"def\s+\w+\s*\(.*?\):.*?(?=\n\n|\Z)", code_content, re.DOTALL)
        
        if not code_blocks and not code_content.strip().startswith('def'):
             # Если код - это просто инструкции, добавим заглушку функции main
             code_content = f"def main():\n{code_content}"
             entry_point = "main"

        try:
            # 1. Запись кода во временный файл
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(code_content)
                # Добавляем вызов точки входа для исполнения
                tmp.write(f"\n\nif '{entry_point}' in globals():\n    print(f'>>> Executing entry point: {entry_point} <<<')\n    try:\n        {entry_point}()\n    except TypeError:\n        # Если функция принимает аргументы, вызываем без них для простого теста\n        {entry_point}(*{args}, **{kwargs})\n")
                tmp_path = tmp.name

            # 2. Исполнение кода как модуля
            runpy.run_path(tmp_path, run_name="__main__")
            
            log_str = captured_output.getvalue()
            log_output = log_str
            
            # Проверка на успех: если код выполнился без исключений
            if "Traceback" not in log_str and "Error" not in log_str and "Exception" not in log_str:
                 success = True

        except Exception as e:
            # Захватываем исключения, произошедшие при запуске runpy
            log_output = captured_output.getvalue()
            log_output += f"\n--- CRITICAL RUNTIME ERROR ---\nException: {type(e).__name__}: {e}"
            success = False
        finally:
            # 3. Восстановление stdout и удаление временного файла
            sys.stdout = original_stdout
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            
        return success, log_output