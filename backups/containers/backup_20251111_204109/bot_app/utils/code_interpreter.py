# utils/code_interpreter.py
import logging
import subprocess
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class CodeInterpreter:
    """
    Инструмент для безопасной работы с файловой системой и выполнения кода/тестов.
    """

    def __init__(self, base_path: str = "./", interpreter_timeout: int = 15):
        self.base_path = base_path
        self.interpreter_timeout = interpreter_timeout

    def write_file(self, filename: str, content: str) -> str:
        """Безопасно записывает содержимое в файл."""
        full_path = self.base_path + filename
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Файл '{full_path}' успешно записан."
        except Exception as e:
            logger.error(f"Ошибка записи файла {full_path}: {e}")
            return f"ОШИБКА: Не удалось записать файл {full_path}. {e}"

    def safe_execute_code(self, code: str, context: str = "main_function") -> Tuple[bool, str]:
        """
        Безопасное выполнение фрагмента кода Python с ограниченными встроенными функциями.
        (Использует логику из intelligent_agent.py для консистентности)
        """
        if not code or not code.strip():
            return False, "Пустой код"
        
        # Безопасный контекст (аналогичен intelligent_agent.py)
        safe_globals = {
            '__name__': '__main__',
            '__builtins__': {
                'print': print, 'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set, 'range': range,
                'Exception': Exception, 'AssertionError': AssertionError,
                'TypeError': TypeError, 'ValueError': ValueError, 'KeyError': KeyError,
                'isinstance': isinstance, 'hasattr': hasattr, 'getattr': getattr, 'setattr': setattr,
                'issubclass': issubclass, 'callable': callable,
                'abs': abs, 'min': min, 'max': max, 'sum': sum, 'round': round,
            }
        }
        
        try:
            # Проверка синтаксиса
            compile(code, '<string>', 'exec')
            
            # Выполнение кода
            exec(code, safe_globals, {})
            return True, f"Код ({context}) выполнен успешно."
        except SyntaxError as e:
            logger.warning(f"Syntax error in {context}: {e}")
            return False, f"Синтаксическая ошибка ({context}): {e}"
        except Exception as e:
            logger.error(f"Execution error in {context}: {e}")
            return False, f"Ошибка выполнения ({context}): {str(e)}"

    def run_unit_tests(self, filename: str) -> str:
        """
        Запускает тесты с использованием subprocess (имитация pytest).
        ВНИМАНИЕ: Для реального использования pytest должен быть установлен в контейнере!
        """
        try:
            # Имитация запуска теста
            result = subprocess.run(
                ["python", filename],
                capture_output=True,
                text=True,
                timeout=self.interpreter_timeout,
                check=False
            )
            
            if result.returncode != 0:
                # Ошибка выполнения или проваленные тесты
                return f"Тесты провалены (Код выхода: {result.returncode}).\nStdout: {result.stdout}\nStderr: {result.stderr}"
            
            return f"Тесты успешно пройдены.\nStdout: {result.stdout}"

        except subprocess.TimeoutExpired:
            return "ОШИБКА: Тесты превысили лимит времени."
        except FileNotFoundError:
            return "ОШИБКА: Файл для тестирования не найден."
        except Exception as e:
            return f"КРИТИЧЕСКАЯ ОШИБКА при запуске тестов: {str(e)}"

# Создадим заглушку для инструмента, который будет использоваться для отчетов
def submit_deployment_report(**kwargs) -> Dict[str, Any]:
    """Заглушка для submit_deployment_report."""
    return {
        "deployment_ready": kwargs.get("deployment_ready", False),
        "description": kwargs.get("patch_description", "Task Manager Report"),
        "tests_status": kwargs.get("tests_status", "N/A"),
        "smoke_test_result": kwargs.get("smoke_test_result", "N/A")
    }